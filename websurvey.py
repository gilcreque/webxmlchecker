from lxml import etree
from lxml import objectify
from lxml.etree import tostring


class Survey:
    """Class for creating survey object"""

    def __init__(self, data):

        root = objectify.fromstring(data)
        self.questionList = []

        for i, webQuestion in enumerate(root.questions.iterchildren()):
            questionLabel = webQuestion['varname'].text
            setattr(self, questionLabel,
                    Question(i, webQuestion.iterchildren()))
            self.questionList.append(getattr (self, questionLabel))

        for i, webQuota in enumerate(root.quotas.iterchildren()):
            quotaLabel = "quota_" + str(i)
            setattr(self, quotaLabel,
                    Quota(i, webQuota.iterchildren()))


class Question:
    """Class for questions in survey"""

    def __init__(self, order, iterator):

        self.order = order
        for attribute in iterator:
            if attribute.tag == "responses":
                setattr(self, attribute.tag,
                Response(attribute.iterchildren()))
            else:
                attrvalue = attribute.text
                if attribute.tag == "filter" and attrvalue == "TN":
                    attrvalue = False
                elif attrvalue == 'true':
                    attrvalue = True
                elif attrvalue == 'false':
                    attrvalue = False
                elif isinstance(attrvalue, str):
                    try:
                        attrvalue = int(attrvalue)
                    except ValueError:
                        pass
                setattr(self, attribute.tag, attrvalue)


class Response:
    """Class for responses in survey"""

    def __init__(self, iterator):

        responseCodeDict = {}
        for i, attribute in enumerate(iterator):
            responseCode = "_" + attribute['code'].text
            responseCodeDict[responseCode] = {}
            responseCodeDict[responseCode]["order"] = i
            responseAttr = (
            "islogic", "logic", "text", "terminate", "scramble")
            for attrb in responseAttr:
                attrvalue = attribute[attrb].text
                if attrvalue == 'true':
                    attrvalue = True
                elif attrvalue == 'false':
                    attrvalue = False
                elif isinstance(attrvalue, str):
                    try:
                        attrvalue = int(attrvalue)
                    except ValueError:
                        pass
                responseCodeDict[responseCode][attribute[attrb].tag] = (
                                 attrvalue)
        for k, v in responseCodeDict.iteritems():
            setattr(self, k, ResponseCode(v))


class ResponseCode:
    """Class for response codes in survey"""

    def __init__(self, attrbDict):

        for k, v in attrbDict.iteritems():
            setattr(self, k, v)


class Quota:
    """Class for quotas in survey"""

    def __init__(self, order, iterator):

        self.order = order
        for attribute in iterator:
            if attribute.tag == "max":
                tag = "need"
                attrvalue = int(attribute.text)
            elif attribute.tag == "quota":
                tag = "logic"
                attrvalue = attribute.text
            elif attribute.tag == "quota_name":
                tag = "name"
                attrvalue = attribute.text
            setattr(self, tag, attrvalue)
