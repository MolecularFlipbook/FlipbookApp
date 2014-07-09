import os

def make_zip_file(input_directory, output_directory=None, output_name=None):
    import zipfile                                                              
    import glob                                                                 
    import fnmatch                                                              
    import tempfile                                                             

    if not os.path.exists(input_directory):
        print "ERROR: Input make_zip directory " + input_directory + " does not exist!"
        return 'stop'

    if output_name == None:                              
        name = os.path.basename(input_directory)                                
    else:                                                                       
        name = os.path.basename(output_name.split(".zip")[0])                   
                                                                                
    zipname = tempfile.mktemp('.zip', name + '_', output_directory)             
    zipname_abs = os.path.abspath(zipname)                                      
                                                                                
    if output_name != None:                                                     
        zipdir = os.path.dirname(zipname_abs)                                   
        zipname = zipdir + os.sep + name + '.zip'                               
        zipname_abs = os.path.abspath(zipname)                                  
                                                                                
    name = os.path.basename(zipname).split('.zip')[0]                           
                                                                                
    z = zipfile.ZipFile(zipname, "w")                                           
    abpath = os.path.abspath(input_directory)                                   
                                                                                
    for root, dirnames, filenames in os.walk(abpath):                           
        for filename in fnmatch.filter(filenames, '*'):                         
            filepath = os.path.join(root, filename)                             
            filename = os.path.basename(filepath)                               
            filedir = os.path.basename(os.path.dirname(filepath))               
            d = root.split(input_directory)[1]                                  
            z.write(filepath, name + os.sep + d + os.sep + filename)            

    z.close()           

    return zipname_abs
