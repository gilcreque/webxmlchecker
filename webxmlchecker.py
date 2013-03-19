#!/usr/bin/env python

import re
import sys
from pprint import pprint
from datetime import datetime

import websurvey


def checkxml(question, checkFile, survey):

    questionWarning = False
    checkFileText = ""

    validCheckedType = ['Category', 'Multiple', 'Numeric', 'OpenEnd',
                        'OpenEndBig']
    validNotCheckedType = ['Display', 'Calculation', 'Random']

    if question.type in validCheckedType:
        if not question.validate:
            checkFileText += (question.varname + " is a " + question.type +
                            " type and validate is not checked\n")
            questionWarning = True
    elif question.type in validNotCheckedType:
        if question.validate:
            checkFileText += (question.varname + " is a " + question.type +
                            " type and validate is checked\n")
            questionWarning = True

    locationGTZero = ['Category', 'Multiple', 'Numeric', 'OpenEnd',
                      'OpenEndBig', 'Calculation', 'Random']
    locationZero = ['Display']

    if question.type in locationGTZero and question.displayType != "Grid":
        if question.location < 1:
            checkFileText += (question.varname + " is a " + question.type +
                            " type and location is less than one\n")
            questionWarning = True
    elif (question.type in locationZero) or (question.type == "Category" and
                                            question.displayType == "Grid"):
        if question.location != 0:
            checkFileText += (question.varname + " is a Grid Display and " +
                            "location is not zero\n")
            questionWarning = True

    lengthGTZero = ['Category', 'Multiple', 'Numeric',
                    'Calculation', 'Random']
    lengthZero = ['Display']
    lengthDefault = {'OpenEnd': 2, 'OpenEndBig': 20}

    if question.type in lengthGTZero and question.displayType != "Grid":
        if question.length < 1:
            checkFileText += (question.varname + " is a " + question.type +
                            " type and length is less than one\n")
            questionWarning = True
    elif (question.type in lengthZero) or (question.type == "Category" and
                                            question.displayType == "Grid"):
        if question.length != 0:
            checkFileText += (question.varname + " is a Grid Display and " + 
                            "length is not zero\n")
            questionWarning = True
    for k, v in lengthDefault.iteritems():
        if question.type == k and question.length != v:
            checkFileText += (question.varname + " is a " + k +
                     " type and length is not default(" + str(v) + ")\n")
            questionWarning = True

    numMultGTZero = ['Category', 'Multiple', 'Numeric',
                    'Calculation']
    numMultDefault = {'OpenEnd': 2, 'OpenEndBig': 10, 'Display': 1,
                    'Random': 1}

    if question.type in numMultGTZero:
        if question.num_responses < 1:
            checkFileText += (question.varname + " is a " + question.type +
                            " type and NumMult is less than one\n")
            questionWarning = True
    for k, v in numMultDefault.iteritems():
        if question.type == k and question.num_responses != v:
            checkFileText += (question.varname + " is a " + k +
                     " type and NumMult is not default(" + str(v) + ")\n")
            questionWarning = True

    if question.filter is None:
        checkFileText += (question.varname + " has a blank filter\n")
        questionWarning = True
    elif question.filter:
        filterGroups = re.findall(
                         '([A-Za-z+][A-Za-z0-9]*\([A-Za-z0-9,-]+\))',
                         question.filter)
        #print question.varname, ' '.join(filterGroups)
        for logic in filterGroups:
            notInRange = False
            notInRangeList = []
            questionMatch = re.search(
                          '([A-Za-z+][A-Za-z0-9]*(?=\([A-Za-z0-9,-]+\)))'
                          , logic).group(0)
            try:
                questionCheck = getattr (survey, questionMatch)
            except (AttributeError):
                checkFileText += (question.varname + " filter error: " + "\"" +
                                questionMatch +
                                "\" is not a valid question\n")
                questionWarning = True
                break
            
            punchesMatch = re.split(",", re.search('(?<=\()([A-Za-z0-9,-]+)',
                            logic).group(0))
            for punches in punchesMatch:
                findRange = re.search('([0-9]+)(-)([0-9]+)', punches)
                if findRange:
                    punchLength = len(findRange.group(3))
                    rangeLow = int(findRange.group(1))
                    rangeHigh = int(findRange.group(3))+1
                    punchesMatch.remove(punches)
                    for i in range (rangeLow, rangeHigh): 
                        punchesMatch.append(str(i).zfill(punchLength))
            #print punchesMatch
            for punches in punchesMatch:
                try:
                    getattr (getattr (questionCheck, "responses"), "_"+punches)
                except (AttributeError):
                    if questionCheck.type == "Numeric":
                        try:
                            checkPunches = int(punches)
                            numRange = range (questionCheck.min, 
                                              questionCheck.max+1)
                            #print checkPunches, numRange
                            if checkPunches not in numRange:
                                raise ValueError
                        except ValueError:
                            notInRange = True
                            notInRangeList.append(punches)
                    else:
                        checkFileText += (question.varname + " filter error: " +
                                        "\"" + punches +
                                        "\" is not a valid response for " +
                                        questionMatch + "\n")
                        questionWarning = True
            if notInRange:
                checkFileText += (question.varname + " filter error: \"" +
                                ", ".join(notInRangeList) +
                                "\" not within range for " + questionMatch +
                                "\n")
                questionWarning = True
    
    if questionWarning == True:
        dashText = ("-"*((78-len(question.varname))/2)) + " "
        dashText += question.varname + " "
        dashText += ("-"*(((78-len(question.varname)) + 2 / 2) / 2))   
        
        checkFile.write("\n" + dashText + "\n" + checkFileText + "\n")


def main():


    #check to see that minimum arguments were given
    if (len(sys.argv) == 1):
        print "Usage: " + sys.argv[0] + " xmlFileName"
        exit(2)

    xmlFileName = sys.argv[1]

    #check if xml file exists and can be opened
    try:
        data = (open(xmlFileName, 'r')).read()
    except (IOError, NameError):
        print "xmlFileName: " + xmlFileName + " not found"
        exit(2)

    #set filenames
    baseName = re.sub('\.[^.]*$', '', xmlFileName)
    resultFileName = baseName + "_check.txt"

    survey = websurvey.Survey(data)

    try:
        # This will create a new file or **overwrite an existing file**.
        checkFile = open(resultFileName, "wr+")
        checkFile.truncate()
        checkFile.write("Runtime: " + 
                        str(datetime.now().strftime('%a %b %d %Y %I:%M:%S%p'))
                        + "\n")

        try:
            for question in survey.questionList:
                checkxml(question, checkFile, survey)

        finally:
            checkFile.close()

    except IOError:
        print "could not create/overwrite: " + resultFileName
        pass

if __name__ == '__main__':
    main()
