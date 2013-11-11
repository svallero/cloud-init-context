#!/usr/bin/python

from base64 import b64encode 
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
import fileinput 
import gzip
import ntpath
import os
import string
import sys
import textwrap
import urllib2

import yaml
import yaml.constructor
try:
    # included in standard lib from Python 2.7
    from collections import OrderedDict
except ImportError:
    # try importing the backported drop-in replacement
    # it's available on PyPI
    from ordereddict import OrderedDict
 

# Remember to add below all the standard modules you intend to use 
# (better to put all...) TODO
standard_modules = ['packages', 'runcmd', 'yum_repos', 'bootcmd', 'preserve_hostname', 'hostname', 'yum_repos', 'write_files']

#########################################
class OrderedDictYAMLLoader(yaml.Loader):

    # A YAML loader that loads mappings into ordered dictionaries
    # (default is alphabetical order)
 
    def __init__(self, *args, **kwargs):
        yaml.Loader.__init__(self, *args, **kwargs)
 
        self.add_constructor(u'tag:yaml.org,2002:map', type(self).construct_yaml_map)
        self.add_constructor(u'tag:yaml.org,2002:omap', type(self).construct_yaml_map)
 
    def construct_yaml_map(self, node):
        data = OrderedDict()
        yield data
        value = self.construct_mapping(node)
        data.update(value)
 
    def construct_mapping(self, node, deep=False):
        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        else:
            raise yaml.constructor.ConstructorError(None, None,
                'expected a mapping node, but found %s' % node.id, node.start_mark)
 
        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError, exc:
                raise yaml.constructor.ConstructorError('while constructing a mapping',
                    node.start_mark, 'found unacceptable key (%s)' % exc, key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping

########################################
def represent_ordereddict(dumper, data):
    # This is to dump loaded dictionaries in order
    value = []

    for item_key, item_value in data.items():
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)

        value.append((node_key, node_value))

    return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)

yaml.add_representer(OrderedDict, represent_ordereddict)

###############################
def joinheader(header, module):
   tmpfile= open("/tmp/tmphandler.py", "w")
   for line in module.readlines():
      if line.startswith('response = urllib2.urlopen'):
        continue
      elif line.startswith('exec (response.read())'):
         tmpfile.write(header.read())
      else:
         tmpfile.write(line)
    
   tmpfile.close()
   tmpfile= open("/tmp/tmphandler.py", "r")
   content = tmpfile.read()
   tmpfile.close()
   return content 

###########################
def reindent(s, numSpaces):
    s = string.split(s, '\n')
    s = [(numSpaces * ' ') + string.rstrip(line) for line in s]
    s = string.join(s, '\n')
    return s

###########################################
def get_file_content_repo(filename, reponame):
    os.system('wget -O /tmp/'+filename+' '+reponame+'/'+filename+'') 
    f = open('/tmp/'+filename+'', 'r')  
    value = f.read()
    return value

#############################
def get_file_content(filename):
    f = open(filename, 'r')  
    value = f.read()
    return value

# Main function
combined_message = MIMEMultipart()
combined = ''
for line in fileinput.input():
   (filename, format_type) = line.split(":", 1)
   # User defined cloud-config
   if 'multiple-config' in format_type:
      with open(filename) as fh:
         contents = fh.read()
         # Load contents in order with custom loader
         items = yaml.load(textwrap.dedent(contents), OrderedDictYAMLLoader)
         for i in items:
            # Copy part-handler content directly in MIME
            # taken from web server, add possibility to take from local TODO 
            if i == 'parthandlers':
               format_type='part-handler'  
               handlers_cfg = items[i] 
               repo = handlers_cfg['repo']
               header = handlers_cfg['header']
               summary = handlers_cfg['header']
               for mod in handlers_cfg['modules']: 
                 filename = mod
                 header_content = urllib2.urlopen(''+repo+'/'+header+'') 
                 module_content = urllib2.urlopen(''+repo+'/'+mod+'')
                 contents=joinheader(header_content, module_content)   
                 #contents = module_content.read()
                 sub_message = MIMEText(contents, format_type, sys.getdefaultencoding())
                 sub_message.add_header('Content-Disposition', 'attachment; filename="%s"' % (filename))
	         #encoders.encode_base64(sub_message)
                 combined_message.attach(sub_message)

            # Copy afterburner content directly in MIME 
            # afterburner should be scripts (shell, python etc...)
            # If starting with 'http' they are fetched from server
            # else from local path.
            if i == 'afterburners' or i == 'boothook':
               burners_cfg = items[i] 
               for script in burners_cfg: 
                 format_type='x-shellscript'  
                 if i == 'boothook':
                   format_type='cloud-boothook'  
                 head, tail = ntpath.split(script)
                 filename=tail 
                 if script.startswith('http'): 
                    content = urllib2.urlopen(script)
                    contents = content.read() 
                 else:
                    contents = get_file_content(script) 
                     
                 #contents = module_content.read()
                 sub_message = MIMEText(contents, format_type, sys.getdefaultencoding())
                 sub_message.add_header('Content-Disposition', 'attachment; filename="%s"' % (filename))
	         #encoders.encode_base64(sub_message)
                 combined_message.attach(sub_message)
                
            # Else make one MIME entry for each config block    
            else:
                single = items[i]
                #assert type(single) is OrderedDict
                #print (single)
                contents =  yaml.dump(single,line_break="\n",
                        indent=4,
                        explicit_start=False,
                        explicit_end=False,
                        default_flow_style=False)
                if i not in standard_modules:
                  format_type = (''+i+'-config')
                  if 'embedfiles' in contents:
                    files = single['embedfiles']
                    if 'repo' in contents:
                      repo = single['repo']
                      if 'files' not in contents:
                        del single['repo'] 
                    for file in files:
                      if file.startswith('+'):
                        # remove the first character
                        file = file[1:]
                        if repo:
                          filecontent = get_file_content_repo(file, repo)  
                        else:  
                          print ('ERROR: repo is not specified in '+i+' block!') 
                          exit
                      else:   
                        filecontent = get_file_content(file) 
                        head, tail = ntpath.split(file) 
                        file=tail
                      single[file]=filecontent.strip()
                    del single['embedfiles'] 
                
                else:
                  format_type = ('cloud-config')
            
                # re-dump in yaml format
                contents =  yaml.dump(single,line_break="\n",
                        indent=4,
                        explicit_start=False,
                        explicit_end=False,
                        default_flow_style=False)
                # piccolo patch perche' il formato in MIME rispecchi
                # quello del file di configurazione, solo estetica
                append = (''+i+': \n') 
                contents = ''.join((append, reindent(contents,2)))
                filename = (''+i+'-config.ccfg')
                sub_message = MIMEText(contents, format_type, sys.getdefaultencoding())
                sub_message.add_header('Content-Disposition', 'attachment; filename="%s"' % (filename))
	        #encoders.encode_base64(sub_message)
                combined_message.attach(sub_message)
              
           
   else: 
      with open(filename) as fh:
         contents = fh.read()
         sub_message = MIMEText(contents, format_type, sys.getdefaultencoding())
         sub_message.add_header('Content-Disposition', 'attachment; filename="%s"' % (filename))
	 #encoders.encode_base64(sub_message)
         combined_message.attach(sub_message)

# Encode in base 64
output = b64encode(combined_message.as_string())
# Write output file
ofilename = 'userdata.txt.gz'
ofile = open(ofilename,"wb")
#ofile.write(output)
#ofile.write(combined_message.as_string())
# Gzipped
gfile = gzip.GzipFile(fileobj=ofile, filename = (ofilename))
gfile.write(combined_message.as_string())
#gfile.write(output) # base64 encoded
gfile.close()
ofile.close()

#print(combined_message)
