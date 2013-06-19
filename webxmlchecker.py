#!/usr/bin/env python

import re
import sys
from pprint import pprint
from datetime import datetime

import websurvey

def check_question_validate_checkbox(question):

    _check_file_text = ""
    _valid_checked_type = ['Category', 'Multiple', 'Numeric', 'OpenEnd',
                        'OpenEndBig']
    _valid_not_checked_type = ['Display', 'Calculation', 'Random']

    if question.type in _valid_checked_type:
        if not question.validate:
            _check_file_text += (question.varname + " is a " + question.type +
                            " type and validate is not checked\n")
            return True, _check_file_text
    elif question.type in _valid_not_checked_type:
        if question.validate:
            _check_file_text += (question.varname + " is a " + question.type +
                            " type and validate is checked\n")
            return True, _check_file_text
    return False,


def check_question_location(question):

    _check_file_text = ""
    _location_gt_zero = ['Category', 'Multiple', 'Numeric', 'OpenEnd',
                      'OpenEndBig', 'Calculation', 'Random']
    _location_zero = ['Display']

    if question.type in _location_gt_zero and question.displayType != "Grid":
        if question.location < 1:
            _check_file_text += (question.varname + " is a " + question.type +
                            " type and location is less than one\n")
            return True, _check_file_text
    elif (question.type in _location_zero) or (question.type == "Category" and
                                            question.displayType == "Grid"):
        if question.location != 0:
            _check_file_text += (question.varname + " is a Grid Display and " +
                            "location is not zero\n")
            return True, _check_file_text
    return False,


def check_question_length(question):

    _check_file_text = ""
    _length_gt_zero = ['Category', 'Multiple', 'Numeric',
                    'Calculation', 'Random']
    _length_zero = ['Display']
    _length_default = {'OpenEnd': 2, 'OpenEndBig': 20}

    if question.type in _length_gt_zero and question.displayType != "Grid":
        if question.length < 1:
            _check_file_text += (question.varname + " is a " + question.type +
                            " type and length is less than one\n")
            return True, _check_file_text
    elif (question.type in _length_zero) or (question.type == "Category" and
                                            question.displayType == "Grid"):
        if question.length != 0:
            _check_file_text += (question.varname + " is a Grid Display and " + 
                            "length is not zero\n")
            return True, _check_file_text
    for k, v in _length_default.iteritems():
        if question.type == k and question.length != v:
            _check_file_text += (question.varname + " is a " + k +
                     " type and length is not default(" + str(v) + ")\n")
            return True, _check_file_text
    return False,


def check_question_nummult(question):

    _check_file_text = ""
    _nummult_gt_zero = ['Category', 'Multiple', 'Numeric',
                    'Calculation']
    _nummult_default = {'OpenEnd': 2, 'OpenEndBig': 10, 'Display': 1,
                    'Random': 1}

    if question.type in _nummult_gt_zero:
        if question.num_responses < 1:
            _check_file_text += (question.varname + " is a " + question.type +
                            " type and NumMult is less than one\n")
            _question_warning_flag = True
            return True, _check_file_text
    for k, v in _nummult_default.iteritems():
        if question.type == k and question.num_responses != v:
            _check_file_text += (question.varname + " is a " + k +
                     " type and NumMult is not default(" + str(v) + ")\n")
            _question_warning_flag = True
            return True, _check_file_text
    return False,


def check_logic(name, typename, logic, survey):

    _check_file_text = ""
    _logic_groups = re.findall(
                     '([A-Za-z+][A-Za-z0-9]*\([A-Za-z0-9,-]+\))', logic)
    #print name, ' '.join(_logic_groups)
    for logic in _logic_groups:
        notInRange = False
        notInRangeList = []
        questionMatch = re.search(
                      '([A-Za-z+][A-Za-z0-9]*(?=\([A-Za-z0-9,-]+\)))'
                      , logic).group(0)
        try:
            questionCheck = getattr (survey, questionMatch)
        except (AttributeError):
            _check_file_text += (name + " " + typename + " error: " + 
                                "\"" + questionMatch +
                                "\" is not a valid question\n")
            return True, _check_file_text
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
                    _check_file_text += (name + " " + typename +
                                        " error: " + "\"" + punches +
                                        "\" is not a valid response for " +
                                        questionMatch + "\n")
                    return True, _check_file_text
        if notInRange:
            _check_file_text += (name + " " + typename + " error: \"" +
                                ", ".join(notInRangeList) +
                                "\" not within range for " +
                                questionMatch + "\n")
            return True, _check_file_text
    return False,
        
        
def check_filter_logic(question, survey):
    if question.filter is None:
        _check_file_text = (question.varname + " has a blank filter\n")
        return True, _check_file_text
    elif question.filter:
        return check_logic(question.varname, "filter", question.filter, survey)
    else:
        return False,

def check_question(question, checkFile, survey):

    _question_warning_flag = False
    _check_file_text = ""

    validate = check_question_validate_checkbox(question)
    location = check_question_location(question)
    length = check_question_length(question)
    nummult = check_question_nummult(question)
    filterlogic = check_filter_logic(question, survey)

    check_question_list = [validate, location, length, nummult, filterlogic]

    for i, checks in enumerate(check_question_list):
        if checks[0]:
            _question_warning_flag = True
            _check_file_text += checks[1]          
    if _question_warning_flag:
        dashText = ("-"*((78-len(question.varname))/2)) + " "
        dashText += question.varname + " "
        dashText += ("-"*(((78-len(question.varname)) + 2 / 2) / 2))   
        checkFile.write("\n" + dashText + "\n" + _check_file_text + "\n")


def check_quota_logic(quota, checkFile, survey):
    quotalogic = check_logic(quota.name, "quota", quota.logic, survey)
    if quotalogic[0]:
        dashText = ("-"*((78-len(quota.name))/2)) + " "
        dashText += quota.name + " "
        dashText += ("-"*(((78-len(quota.name)) + 2 / 2) / 2))   
        checkFile.write("\n" + dashText + "\n" + quotalogic[1] + "\n")


def main():


    #check to see that minimum arguments were given
    if (len(sys.argv) == 1):
        sys.stderr.write("Usage: " + sys.argv[0] + " xmlFileName\n")
        exit(2)

    xmlFileName = sys.argv[1]

    #check if xml file exists and can be opened
    try:
        data = (open(xmlFileName, 'r')).read()
    except (IOError, NameError):
        sys.stderr.write("xmlFileName: " + xmlFileName + " not found\n")
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
                check_question(question, checkFile, survey)
            for quota in survey.quotaList:
                check_quota_logic(quota, checkFile, survey)

        finally:
            checkFile.close()
            
    except IOError, e:
        sys.stderr.write("could not create/overwrite: " + resultFileName + '\n')
        sys.stderr.write(str(e) + '\n')        
        exit(2)

if __name__ == '__main__':
    main()
