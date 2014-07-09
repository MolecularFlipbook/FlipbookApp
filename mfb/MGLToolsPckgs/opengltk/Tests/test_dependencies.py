#
#################################################################
#       Author: Sowjanya Karnati
#################################################################
#
#Purpose:To update dependencies list
#
# $Id: test_dependencies.py,v 1.3 2006/03/15 21:43:34 sowjanya Exp $
from mglutil.TestUtil.Tests.dependenciestest import DependencyTester
import unittest
d = DependencyTester()
result_expected =[]
class test_dep(unittest.TestCase):
    
    def test_dep_1(self):
        result = d.rundeptester('opengltk')    
        if result !=[]:
            print "\nThe Following Packages are not present in CRITICAL or NONCRITICAL DEPENDENCIES of opengltk :\n  %s" %result
            self.assertEqual(result,result_expected) 
        else:
            self.assertEqual(result,result_expected)
    

if __name__ == '__main__':
    unittest.main()


