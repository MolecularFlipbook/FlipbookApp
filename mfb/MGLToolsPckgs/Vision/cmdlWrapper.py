#
# Author Michel Sanner
#
# generate wrapper code for command line programs
#

class wrapperGenerator:
    """Generates wraper code from a desciption of a command line"""

    def __init__(self, filename):
        f = open(filename, 'r')
        lines = f.readlines()
        f.close()

        self.descr = {}
        self.inputs = []
        self.outputs = []
        lastDescrIn = None
        lastDescrOut = None
        self.params = {}
        
        for line in lines:
            if len(line)<2: continue
            if line[0]=='#': continue
            
            key = line.split(' ')[0]

            if key in ['nodename', 'nodedoc', 'binary']:
                if lastDescrIn:
                    self.inputs.append(lastDescrIn)
                    lastDescrIn = None
                if lastDescrOut:
                    self.outputs.append(lastDescrOut)
                    lastDescrOut = None

                k,v = line.split('=')
                self.descr[k.strip()] = v.strip()

            elif key=='input':
                if lastDescrIn:
                    self.inputs.append(lastDescrIn)
                    lastDescrIn = None
                if lastDescrOut:
                    self.outputs.append(lastDescrOut)
                    lastDescrOut = None
                lastDescrIn = {}

                for block in line[6:].strip().split(','):
                    if '=' in block:
                        k,v = block.split('=')
                        lastDescrIn[k.strip()] = v.strip()

            elif key=='output':
                if lastDescrIn:
                    self.inputs.append(lastDescrIn)
                    lastDescrIn = None
                if lastDescrOut:
                    self.outputs.append(lastDescrOut)
                    lastDescrOut = None
                lastDescrOut = {}

                for block in line[6:].strip().split(','):
                    if '=' in block:
                        k,v = block.split('=')
                        lastDescrOut[k.strip()] = v.strip()
            else:
                if lastDescrIn:
                    for block in line[6:].strip().split(','):
                        if '=' in block:
                            k,v = block.split('=')
                            lastDescrIn[k.strip()] = v.strip()
                elif lastDescrOut:
                    for block in line[6:].strip().split(','):
                        if '=' in block:
                            k,v = block.split('=')
                            lastDescrOut[k.strip()] = v.strip()
                    
        if lastDescrIn:
            self.inputs.append(lastDescrIn)
        if lastDescrOut:
            self.outputs.append(lastDescrOut)

    def codeGen(self):
        # call signature and command string
        callSignature = """"""
        printVar = """"""
        cmdString = self.descr['binary']+' '

        for ipdescr in self.inputs:
            name = ipdescr['name']

            dtype =  ipdescr['type']
            if dtype=='float' or dtype=='int':
                format = '%g'
            elif dtype in ['string', 'str', 'file', 'choice']:
                format = '%s'

            default = ipdescr.get('defaultValue', None)
            if default:
                callSignature += name+' = %s, '%default
            else:
                callSignature += name+', '
            printVar += name+', '

            cmdString += ipdescr['argument'].replace('%value%', format)+' '

        cmdString = '"'+cmdString[:-1]+'"%('+printVar[:-2]+')'

        # cmdString
        code = """from popen2 import Popen4
class %s:

    def __init__(self):
        self.params = %s

    def __call__(self, %s):
        exec_cmd = Popen4(%s)
        status = exec_cmd.wait()
        out = err = None
        if status==0:
            out = exec_cmd.fromchild.read()
        else:
            err = exec_cmd.childerr.read()
        return (status, out, err)
""" % (self.descr['nodename'], repr(self.params), callSignature[:-2],
       cmdString)

        return code

if __name__=='__main__':
    wg = wrapperGenerator('../descr.py')
    code = wg.codeGen()
    f = open('test.py', 'w')
    map(lambda l, f=f: f.write("%s"%l), code)
    f.close()
