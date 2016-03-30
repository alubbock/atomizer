from utils import readBNGXML
import argparse
from utils import extractAtomic
from collections import defaultdict,Counter


def extractCenterContext(rules, excludeReverse=False):
    transformationCenter = []
    transformationContext = []
    transformationProduct = []
    atomicArray = []
    actionNames = []
    label = []
    doubleModificationRules = []
    for idx, rule in enumerate(rules):
        tatomicArray, ttransformationCenter, ttransformationContext, \
            tproductElements, tactionNames, tlabelArray = extractAtomic.extractTransformations(
                [rule], True)
        if excludeReverse and '_reverse_' in rule[0].label:
            continue
        label.append(rule[0].label)

        if len([x for x in tactionNames if 'ChangeCompartment' not in x]) > 1:
            doubleModificationRules.append(rule[0].label)
        transformationCenter.append(ttransformationCenter)
        transformationContext.append(ttransformationContext)

        actionNames.append(tactionNames)
        atomicArray.append(tatomicArray)
        transformationProduct.append(tproductElements)
    return label, transformationCenter, transformationContext, \
        transformationProduct, atomicArray, actionNames, doubleModificationRules


def getStateTransitionDiagram(labels, centers, products, contexts, actions, molecules, rules, parameters):
    def isActive(state):
        return '!' in state or ('~' in state and '~0' not in state)

    moleculeDict = defaultdict(list)

    for molecule in molecules:
        for component in molecule.components:
            moleculeDict[molecule.name].append(component.name)
    nodeList = defaultdict(set)
    edgeList = defaultdict(set)
    for label, center, product, context, action, rule in zip(labels, centers, products, contexts, actions, rules):
        sourceCounter = {}
        destinationCounter = {}

        tmpSourceCounter = defaultdict(Counter)
        tmpContext = {}
        flag = True

        for centerUnit, productUnit, actionUnit, contextUnit in zip(center, product, action, context):
            # create a node label based on reactant + context/ product + context
            if 'ChangeCompartment' in actionUnit:
                continue
            if not flag:
                for species in centerUnit:
                    for element in species.split('.'):
                        if element.split('(')[0].split('%')[0] not in sourceCounter:
                            sourceCounter[element.split('(')[0].split('%')[0]] = Counter()
                            for component in moleculeDict[element.split('(')[0].split('%')[0]]:
                                sourceCounter[element.split('(')[0].split('%')[0]][component] = 0
                        if isActive(element.split('(')[1][:-1]):
                            componentName = element.split('(')[1][:-1].split('~')[0].split('!')[0]
                            tmpSourceCounter[element.split('(')[0].split('%')[0]][componentName] += centerUnit[species]
            else:
                for species in centerUnit:
                    for element in species.split('.'):
                        if element.split('(')[0].split('%')[0] not in sourceCounter:
                            sourceCounter[element.split('(')[0].split('%')[0]] = Counter()
                            for component in moleculeDict[element.split('(')[0].split('%')[0]]:
                                sourceCounter[element.split('(')[0].split('%')[0]][component] = 0
                        if isActive(element.split('(')[1][:-1]):
                            componentName = element.split('(')[1][:-1].split('~')[0].split('!')[0]
                            sourceCounter[element.split('(')[0].split('%')[0]][componentName] += centerUnit[species]
                    tmpContext[species] = contextUnit
                flag = False
            for species in productUnit:
                for element in species.split('.'):
                    if element.split('(')[0].split('%')[0] not in destinationCounter:
                        destinationCounter[element.split('(')[0].split('%')[0]] = Counter()
                        for component in moleculeDict[element.split('(')[0].split('%')[0]]:
                            destinationCounter[element.split('(')[0].split('%')[0]][component] = 0

                    if isActive(element.split('(')[1][:-1]):
                        componentName = element.split('(')[1][:-1].split('~')[0].split('!')[0]
                        destinationCounter[element.split('(')[0].split('%')[0]][componentName] += productUnit[species]
        #add the first context unit
        finalContext = tmpContext[tmpContext.keys()[0]]
        for idx in range(1, len(tmpContext.keys())):
            finalContext[tmpContext.keys()[idx]] -= 1

        for species in finalContext:
        #for speciesUnit in tmpContext:
        #    for species in tmpContext[speciesUnit]:
            for element in species.split('.'):
                if isActive(element.split('(')[1][:-1]):
                    if element.split('(')[0].split('%')[0] in sourceCounter:
                        componentName = element.split('(')[1][:-1].split('~')[0].split('!')[0]

                        sourceCounter[element.split('(')[0].split('%')[0]][componentName] += finalContext[species]
                        destinationCounter[element.split('(')[0].split('%')[0]][componentName] += finalContext[species]

        for element in tmpSourceCounter:
            destinationCounter[element].subtract(tmpSourceCounter[element])
        for molecule in sourceCounter:

            if molecule in destinationCounter:
                localMoleculeCounter =  Counter(moleculeDict[molecule])
                # get total list of nodes. this is important because of symmetric components


                #sourceTuple = tuple(sorted([(x[0], x[1] > 0) for x in sourceCounter[molecule].items()], key=lambda x: x[0]))
                #destinationTuple = tuple(sorted([(x[0], x[1] > 0) for x in destinationCounter[molecule].items()], key=lambda x: x[0]))

                sourceTuple = []
                for x in sourceCounter[molecule].items():
                    sourceTuple.append((x[0], x[1] > 0))
                    for idx in range(1, localMoleculeCounter[x[0]]):
                        sourceTuple.append(('{0}-{1}'.format(x[0], idx+1), x[1] > idx))
                sourceTuple = tuple(sorted(sourceTuple, key=lambda x: x[0]))

                destinationTuple = []
                for x in destinationCounter[molecule].items():
                    destinationTuple.append((x[0], x[1] > 0))
                    for idx in range(1, localMoleculeCounter[x[0]]):
                        destinationTuple.append(('{0}-{1}'.format(x[0], idx+1), x[1] > idx))
                destinationTuple = tuple(sorted(destinationTuple, key=lambda x: x[0]))

                #sourceTuple = tuple(sorted([x[0] for x in sourceCounter[molecule].items()]))
                #destinationTuple = tuple(sorted([x[0] for x in destinationCounter[molecule].items() if x[1]> 0]))

                nodeList[molecule].add(sourceTuple)
                nodeList[molecule].add(destinationTuple)
                parameterList = [parameters[x] if x in parameters else x for x in rule[0].rates]
                edgeList[molecule].add((sourceTuple, destinationTuple, label, ','.join(parameterList)))
        # find the intersection context set
    return nodeList, edgeList

def getContextRequirements(inputfile, collapse=True, motifFlag=False, excludeReverse=False):
    """
    Receives a BNG-XML file and returns the contextual dependencies implied by this file
    """
    molecules, rules, parameters = readBNGXML.parseXML(inputfile)

    moleculeStateMatrix = {}
    label, center, context, product, atomicArray, actions, doubleAction = extractCenterContext(rules, excludeReverse=excludeReverse)
    return getStateTransitionDiagram(label, center, product, context, actions, molecules, rules, parameters)


def getContextRequirementsFromNamespace(namespace, excludeReverse=False):
    label, center, context, product,\
         atomicArray, actions, doubleAction = extractCenterContext(namespace['rules'], excludeReverse=excludeReverse)
    return getStateTransitionDiagram(label, center, product, context, actions, namespace['molecules'], namespace['rules'], namespace['parameters'])



def defineConsole():
    """
    defines the program console line commands
    """
    parser = argparse.ArgumentParser(description='SBML to BNGL translator')
    parser.add_argument('-i', '--input', type=str, help='settings file', required=True)
    return parser


if __name__ == "__main__":
    parser = defineConsole()
    namespace = parser.parse_args()
    inputFile = namespace.input

    stateDictionary = getContextRequirements(inputFile, collapse=True, motifFlag=True)
