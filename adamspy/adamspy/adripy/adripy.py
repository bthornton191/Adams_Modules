"""
--------------------------------------------------------------------------
Description
--------------------------------------------------------------------------
adripy is a set of python tools for manipulating MSC Adams Drill files
--------------------------------------------------------------------------
Author
--------------------------------------------------------------------------
Ben Thornton (ben.thornton@mscsofware.com)
Simulation Consultant - MSC Software
"""
from os import environ
from os import remove
from os import rename
import os.path
import re
import subprocess
import jinja2

env = jinja2.Environment(
    loader=jinja2.PackageLoader('adamspy.adripy', 'templates'),
    autoescape=jinja2.select_autoescape(['evt','str']),
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True
)

# Test that the user config file exists
if 'ADRILL_USER_CFG' not in os.environ:
    raise EnvironmentError('ADRILL_USER_CFG environment variable is not set!')
elif not os.path.exists(os.environ['ADRILL_USER_CFG']):
    raise FileExistsError('The configuration file {} does not exist!  You must set the ADRILL_USER_CFG environment variable to an existing cfg file before importing adripy.'.format(os.environ['ADRILL_USER_CFG']))

# Test that the user shared file exists
if 'ADRILL_SHARED_CFG' not in os.environ:
    raise EnvironmentError('ADRILL_SHARED_CFG environment variable is not set!')
elif not os.path.exists(os.environ['ADRILL_SHARED_CFG']):
    raise FileExistsError('The configuration file {} does not exist!  You must set the ADRILL_SHARED_CFG environment variable to an existing cfg file before importing adripy.'.format(os.environ['ADRILL_SHARED_CFG']))

# Test that the adams launch file exists
if 'ADAMS_LAUNCH_COMMAND' not in os.environ:
    raise EnvironmentError('ADAMS_LAUNCH_COMMAND environment variable is not set!')
elif not os.path.exists(os.environ['ADAMS_LAUNCH_COMMAND']):
    raise FileExistsError('The adams launch file {} does not exist!  You must set the ADRILL_SHARED_CFG environment variable to an existing cfg file before importing adripy.'.format(os.environ['ADAMS_LAUNCH_COMMAND']))


environ['USERPROFILE'] = environ['USERPROFILE']

# Dictionary of TO tool length parameters
TO_LENGTH_PARAM = {}
TO_LENGTH_PARAM['accelerator'] = ['Accelerator_Length']
TO_LENGTH_PARAM['agitator'] = ['Power_Body_Length', 'Shock_Stub_Length']
TO_LENGTH_PARAM['blade_reamer'] = ['Reamer_Length']
TO_LENGTH_PARAM['crossover'] = ['Crossover_Length']
TO_LENGTH_PARAM['dart'] = ['Dart_Length']
TO_LENGTH_PARAM['drill_collar'] = ['Drillcollar_Length']
TO_LENGTH_PARAM['drillpipe'] = ['Pipe_Length']
TO_LENGTH_PARAM['flex_pipe'] = ['Flex_Length']
TO_LENGTH_PARAM['generic_long'] = ['Tool_Length']
TO_LENGTH_PARAM['generic_short'] = ['GenericShort_Length']
TO_LENGTH_PARAM['hw_pipe'] = ['Pipe_Length']
TO_LENGTH_PARAM['instrumentation_sub'] = ['ISUB_Length']
TO_LENGTH_PARAM['jar'] = ['Body_Length', 'Stub_Length']
TO_LENGTH_PARAM['mfr_tool'] = ['Tool_Length']
TO_LENGTH_PARAM['motor'] = ['Motor_Length']
TO_LENGTH_PARAM['mwd_tool'] = ['Tool_Length']
TO_LENGTH_PARAM['pdc_bit'] = ['Bit_Length']
TO_LENGTH_PARAM['single_point'] = ['Bit_Length']
TO_LENGTH_PARAM['roller_cone_bit'] = ['Bit_Length']
TO_LENGTH_PARAM['shock_sub'] = ['Installed_Length']
TO_LENGTH_PARAM['short_collar'] = ['Collar_Length']
TO_LENGTH_PARAM['stabilizer'] = ['Stabilizer_Length']

def turn_measure_on(string_file, tool_types=[], tool_numbers=[], tool_names=[]):
    """
    Modify a string file to turn measure on for the designated tools.  Tools may be designated by type, number (stack order), or name
    
    Parameters
    ----------
    string_file :      Full path to an MSC Adams Drill string file 
                       including the .str extension
    
    tool_types :       List of tool type as seen in the string file
                       (e.g. pdc_bit, motor, stabilizer)
    
    tool_numbers:      List of stack orders corresponding to tools in a string
    
    tool_names:        List of tool names.

                  
    Returns
    -------
    n                  number of tools measured
    """
    n = 0
    mark = False
    with open(string_file,'r') as fid_str, open(string_file.replace('.str','.tmp'),'w') as fid_str_tmp:
        for line in fid_str:
            if line.startswith('$'):
                fid_str_tmp.write(line)

            # If this is a measure line that has been marked
            elif mark and ' measure' in line.lower():
                fid_str_tmp.write(" Measure  =  'yes'\n")
                n += 1
                mark = False
                            
            # Mark if the tool matches a designated stack order
            elif ' stack_order' in line.lower():
                if int(line.replace(' ','').replace('\n','').split('=')[-1]) in tool_numbers:
                    mark = True
                fid_str_tmp.write(line)
            
            # Mark if the tool matches a designated tool type
            elif ' type' in line.lower():
                if line.replace(' ','').replace('\n','').split("'")[-2] in tool_types:
                    mark = True
                fid_str_tmp.write(line)
            
            # Mark if the tool matches a designated tool name
            elif ' name' in line.lower():
                if line.replace(' ','').replace('\n','').split("'")[-2] in tool_names:
                    mark = True
                fid_str_tmp.write(line)
            
            else:
                fid_str_tmp.write(line)

    remove(string_file)
    rename(string_file.replace('.str','.tmp'), string_file)
    return n


def get_tool_name(string_file, tool_type, n=1, return_full_path=True):
    """
    Return the name and file name of the nth tool of type 'tool_type'
    in 'string_file'.
    
    Parameters
    ----------
    string_file :      Full path to an MSC Adams Drill string file 
                       including the .str extension
    
    tool_type :        Tool type as seen in the string file
                       (e.g. pdc_bit, motor, stabilizer)
    
    n :                If the string file has multiple tools of the requested
                       tool type, use this parameter to return the nth tool.
                       Default  is n=1.
    return_full_path : If true, removes the Adrill cdb name and replaces with
                       the adrill cdb file path.  Default is True
                  
    Returns
    -------
    tool_name  :  Name of the requested tool
    tool_file  :  Full file path the the requested tool's property file
    tool_stack :  Stack order of tool
    group_name :  Tools group name if it has one
    """
    tool_found = False
    fid = open(string_file,'r')
    if tool_type == 'hole':
        for line in fid:
            if ' Hole_Property_File  =  ' in line:
                tool_file = line.split("'")[1].replace('/','\\')
                tool_name = tool_file.split('\\')[-1].split('.')[0]
                group_name = tool_name
                if return_full_path:
                    tool_file = get_toolFilename_fullNotation(tool_file)
                tool_found = True
                stack_order = 0
                break
    else:
        count = 0
        for line in fid:
            if ' stack_order' in line.lower():
                stack_order = int(line.replace(' ','').replace('\n','').split('=')[-1])
            elif count == n and ' name ' in line.lower():
                group_name = line.split("'")[1]
            elif count == n and ' property_file' in line.lower():
                tool_file = line.split("'")[1].replace('/','\\')
                tool_name = tool_file.split('\\')[-1].split('.')[0]
                if return_full_path:
                    tool_file = get_toolFilename_fullNotation(tool_file)
                tool_found = True
                break
            elif ' type ' in line.lower() and tool_type.lower() in line.lower():
                count += 1
    
    if tool_found:
        return tool_name, tool_file, stack_order, group_name
    else:
        raise ValueError('Tool of type {} not found in {}'.format(tool_type, string_file))

def get_toolFilename_fullNotation(toolFilename_cdbNotation):
    if '<' in toolFilename_cdbNotation:
        cdb_name = toolFilename_cdbNotation.split('>')[0].replace('<','')
        cdbs = get_adrill_cdbs(os.environ['ADRILL_USER_CFG'], os.environ['ADRILL_SHARED_CFG'])
        if cdb_name in cdbs:
            cdb_path = cdbs[cdb_name]   
            toolFilename_fullNotation = cdb_path + toolFilename_cdbNotation.split('>')[1]                 
        else:
            raise cdbError('ADrill Database {} not defined.'.format(cdb_name))
    else:
        toolFilename_fullNotation = toolFilename_cdbNotation
    return toolFilename_fullNotation


def get_adrill_cdbs(adrill_user_cfg, adrill_shared_cfg=None):
    """
    Return the names and locations of all user defined MSC Adams Drill
    configuration databases (cdbs)
    
    Parameters
    ----------
    adrill_user_cfg : Full path to an MSC Adams Drill user configuration
                      file.  This should be in the HOME directory
                  
    Returns
    -------
    cdbs :  A dictionary with the cdb names as keys and cdb 
            locations as values.
    """
    cdbs = {}
    with open(adrill_user_cfg,'r') as fid:
        for line in fid:
            if line.startswith('DATABASE'):
                # try:
                cdb_name = re.split('[\t ]+',line.lstrip())[1]
                cdb_loc = os.path.normpath(re.split('[\t ]+', line, maxsplit=2)[-1].replace('\n','').replace('$HOME',environ['USERPROFILE']))
                cdbs[cdb_name] = cdb_loc
                # except:
                #     raise cdbError('The following line in {} could not be interpreted.\n\n{}'.format(adrill_user_cfg,line))
    if adrill_shared_cfg:
        top_dir = os.path.split(adrill_shared_cfg)[0]
        with open(adrill_shared_cfg,'r') as fid:
            for line in fid:
                if line.startswith('DATABASE'):
                    # try:
                    cdb_name = re.split('[\t ]+', line, maxsplit=2)[1]
                    cdb_loc = os.path.normpath(re.split('[\t ]+', line, maxsplit=2)[-1].replace('\n','').replace('$HOME',environ['USERPROFILE']).replace('$topdir',top_dir))                        
                    cdbs[cdb_name] = cdb_loc
                    # except:
                        # raise cdbError('The following line in {} could not be interpreted.\n\n{}'.format(adrill_shared_cfg,line))
    return cdbs

def get_TO_param(TO_file, TO_param):
    """
    Return the value of a parameter in a tiem orbit file
    
    Parameters
    ----------
    TO_file :    Full path to a tiem orbit file
    TO_param :   Name of a parameter in TO_file  
                  
    Returns
    -------
    TO_value :  The value assigned to TO_param in TO_file
    """

    # Check if CDB notation used and Convert
    TO_file = get_toolFilename_fullNotation(TO_file)

    param_found = False
    fid = open(TO_file,'r')
    for line in fid:
        if line.lstrip().lower().startswith(TO_param.lower()):
            TO_value = line.replace(' ','').replace('\n','').split('=')[-1]
            param_found = True
            break
    fid.close()
    if param_found:
        return TO_value
    else:
        raise ValueError('{} does not contain the parameter {}'.format(TO_file,TO_param))


def has_tool(string_file, tool_type):
    """
    Returns true if string_file has at least one tool of type tool_type
    
    Parameters
    ----------
    string_file : Full path to an Adams Drill string file
    tool_type :    Adams Drill tool type
                  
    Returns
    -------
    tool_type_found: True if string_file contains at least one tool of type tool_type
    """
    tool_type_found = False
    fid = open(string_file,'r')
    for line in fid:
        if ' Type  =  ' in line and tool_type in line:
            tool_type_found = True
            break
    fid.close()
    return tool_type_found

def fullNotation_to_cdbNotation(string_file):
    """
    Replaces all references in a string file that use full path notation to use CDB notation
    
    Parameters
    ----------
    string_file :       Full path to an Adams Drill string file
                  
    Returns
    -------
    n: Num
    """

    cdbs = get_adrill_cdbs(os.environ['ADRILL_USER_CFG'], os.environ['ADRILL_SHARED_CFG'])
    n = 0 

    with open(string_file, 'r') as fid_str, open(string_file.replace('.str','.tmp'), 'w') as fid_str_tmp:
        for line in fid_str:
            cdb_found = False
            if 'property_file' in line.lower():
                for cdb_name in cdbs:
                    if cdbs[cdb_name] in line:
                        cdb_found = True
                        new_line = line.replace(cdbs[cdb_name], '<{}>'.format(cdb_name))
                        n += 1

                    elif cdbs[cdb_name].replace('\\','/') in line:
                        cdb_found = True
                        new_line = line.replace(cdbs[cdb_name].replace('\\','/'), '<{}>'.format(cdb_name))
                        n += 1

                    elif cdbs[cdb_name].replace('/','\\') in line:
                        cdb_found = True
                        new_line = line.replace(cdbs[cdb_name].replace('/','\\'), '<{}>'.format(cdb_name))
                        n += 1

            if cdb_found:
                fid_str_tmp.write(new_line)
            else:
                fid_str_tmp.write(line)
    
    remove(string_file)
    rename(string_file.replace('.str','.tmp'), string_file)

    return n

def cdbNotation_to_fullNotation(string_file):
    """
    Replaces all references in a string file that use CDB notation to use full path notation
    
    Parameters
    ----------
    string_file :       Full path to an Adams Drill string file
                  
    Returns
    -------
    n: Number of replacements that were made.
    """

    cdbs = get_adrill_cdbs(os.environ['ADRILL_USER_CFG'], os.environ['ADRILL_SHARED_CFG'])
    n = 0 

    with open(string_file, 'r') as fid_str, open(string_file.replace('.str','.tmp'), 'w') as fid_str_tmp:
        for line in fid_str:
            cdb_found = False
            if 'property_file' in line.lower():
                for cdb_name in cdbs:
                    if '<{}>'.format(cdb_name) in line:
                        cdb_found = True
                        new_line = line.replace('<{}>'.format(cdb_name), cdbs[cdb_name].replace('\\','/'))
                        n += 1

            if cdb_found:
                fid_str_tmp.write(new_line)
            else:
                fid_str_tmp.write(line)
    
    remove(string_file)
    rename(string_file.replace('.str','.tmp'), string_file)
    
    return n

def get_cdb_path(full_filepath):    
    """
    Given the full path to a file located in a cdb, get_cdb_path returns the path to a
    file with the cdb path replaced by the cdb alias.  full_filepath will be returned if
    no cdb is found in the path.

    Parameters
    ----------
    full_filepath :     Full file path to a file in a cdb
                  
    Returns
    -------
    cdb_filepath :      Path to a file with the cdb path replaced by the cdb alias.
    """
    cdb_filepath = full_filepath
    cdbs = get_adrill_cdbs(os.environ['ADRILL_USER_CFG'], os.environ['ADRILL_SHARED_CFG'])
    for cdb_name in cdbs:
        if cdbs[cdb_name] in full_filepath:
            cdb_filepath = full_filepath.replace(cdbs[cdb_name], '<{}>'.format(cdb_name))
        elif cdbs[cdb_name].replace('\\','/') in full_filepath:
            cdb_filepath = full_filepath.replace(cdbs[cdb_name].replace('\\','/'), '<{}>'.format(cdb_name))
        elif cdbs[cdb_name].replace('/','\\') in full_filepath:
            cdb_filepath = full_filepath.replace(cdbs[cdb_name].replace('/','\\'), '<{}>'.format(cdb_name))
    return cdb_filepath

def get_full_path(cdb_filepath):    
    """
    Given the cdb path to a file located in a cdb, get_full_path returns the path to a
    file with the cdb alias replaced by the cdb location.

    Parameters
    ----------
    cdb_filepath :     Full file path to a file in a cdb
                  
    Returns
    -------
    full_filepath :      Path to a file with the cdb path replaced by the cdb alias.
    """    

    # Find a string that looks like a database alias
    match = re.search('^<.+>', cdb_filepath)
    
    # Return the given filepath if filepath looks like a full filepath
    if match is None:
        return cdb_filepath
    
    # Pull the database name out of the group
    cdb_name = match.group(0).replace('<', '').replace('>', '')

    # Get a dictionar of the known cdbs
    cdbs = get_adrill_cdbs(os.environ['ADRILL_USER_CFG'], os.environ['ADRILL_SHARED_CFG'])
    
    # Raise an error if cdb_name is not in the cdbs dictionary
    if cdb_name not in cdbs:
        raise ValueError('{} not in {} OR {}!'.format(cdb_name, os.environ['ADRILL_USER_CFG'], os.environ['ADRILL_SHARED_CFG']))
    
    full_filepath = cdb_filepath.replace(match.group(0), cdbs[cdb_name])

    return full_filepath

def get_cdb_location(cdb_name):
    """
    Returns the location of cdb 'cdb_name'

    Parameters
    ----------
    cdb_name :      Alias of a cdb
                  
    Returns
    -------
    cdb_location :  Location of cdb
    """
    cdbs = get_adrill_cdbs(os.environ['ADRILL_USER_CFG'], os.environ['ADRILL_SHARED_CFG'])
    return cdbs[cdb_name]

def replace_tool(string_file, old_tool_file, new_tool_file, old_tool_name='', new_tool_name='', N=0):
    """
    Swaps old_tool_file for new_tool_file in string_file.  Also replaces the tools Name field.
    
    Parameters
    ----------
    string_file :       Full path to an Adams Drill string file
    old_tool_file :     Path to an Adams Drill tool property file that exists in string_file. May use full path or Adrill CDB notation.
    new_tool_file :     Path to an Adams Drill tool property file to replace old_tool_file. May use full path or Adrill CDB notation.
    N :                 Number of replacements to make. Default is 0 which will replace all instances.
    old_tool_name :     Name of the tool to replace. Default is the filename.
    new_tool_name :     Name of the new tool.  Default is the filename.
                  
    Returns
    -------
    n: Number of replacements that were made.
    """
    old_tool_file = old_tool_file.replace('\\','/')
    new_tool_file = new_tool_file.replace('\\','/')
    
    cdbs = get_adrill_cdbs(os.environ['ADRILL_USER_CFG'], os.environ['ADRILL_SHARED_CFG'])
    
    # Get cdb associated with old_tool_file
    old_tool_has_cdb = False
    for cdb_name in cdbs:
        if '<{}>'.format(cdb_name) in old_tool_file or cdbs[cdb_name].replace('\\','/') in old_tool_file:
            old_cdb_name = cdb_name
            old_cdb_loc = cdbs[cdb_name].replace('\\','/')
            old_tool_has_cdb = True
            break
    
    # If old_tool_file uses cdb notation then change it to full path notation
    if '<' in old_tool_file:
        if old_tool_has_cdb:
            old_tool_file = old_tool_file.replace('<{}>'.format(old_cdb_name), old_cdb_loc)
        else:
            raise cdbError('ADrill Database {} not defined.'.format(cdb_name))
                
    # Get cdb associated with new_tool_file
    new_tool_has_cdb = False
    for cdb_name in cdbs:
        if '<{}>'.format(cdb_name) in new_tool_file or cdbs[cdb_name].replace('\\','/') in new_tool_file:
            new_cdb_name = cdb_name
            new_cdb_loc = cdbs[cdb_name].replace('\\','/')
            new_tool_has_cdb = True
            break
    
    # If new_tool_file uses cdb notation then change it to full path notation
    if '<' in new_tool_file:
        if new_tool_has_cdb:
            new_tool_file = new_tool_file.replace('<{}>'.format(new_cdb_name), new_cdb_loc)
        else:
            raise cdbError('ADrill Database {} not defined.'.format(cdb_name))

    if old_tool_name == '':
        old_tool_name = old_tool_file.split('/')[-1].split('.')[0]
    if new_tool_name == '':
        new_tool_name = new_tool_file.split('/')[-1].split('.')[0]
    
    # Open the original string file for reading and a new string file for writing
    fid_oldString = open(string_file,'r')
    fid_newString = open(string_file.replace('.str','.tmp'),'w')

    # Initiate the number of replacements made
    n = 0

    # If the tool is a hole
    if old_tool_file.endswith('.hol'):
        # Loop through the string file to find the hole property file line
        for line in fid_oldString:
            if ' Hole_Property_File  =  ' in line:
                if '<' in line and new_tool_has_cdb:
                    for cdb_name in cdbs:
                        if cdbs[cdb_name].replace('\\','/') in new_tool_file:
                            new_cdb_name = cdb_name
                            new_cdb_loc = cdbs[cdb_name].replace('\\','/')
                            break
                    new_tool_file = new_tool_file.replace(new_cdb_loc, '<' + new_cdb_name + '>')
                fid_newString.write(" Hole_Property_File  =  '{}'\n".format(new_tool_file))
                n += 1
            else:
                fid_newString.write(line)
    
    # If the tool is not a hole
    else:
        # Loop through the string file to find and replace the corresponding tool block
        replace = False
        for line in fid_oldString:
            if ' Type' in line and not line.startswith('$'):
                tool_type = line.split("'")[1]
                fid_newString.write(line)
            elif ' Stack_Order' in line and not line.startswith('$'):
                stack_order = int(line.replace(' ','').replace('\n','').split('=')[1])
                fid_newString.write(line)
            elif " Name  =  '{}".format(old_tool_name) in line and (n<N or N==0):
                if " Name  =  '{}_{:02d}'".format(old_tool_name,stack_order) in line:
                    fid_newString.write(" Name  =  '{}_{:02d}'\n".format(new_tool_name, stack_order))
                else:
                    fid_newString.write(" Name  =  '{}'\n".format(new_tool_name))
                replace = True
            elif ' Property_File' in line and replace and not line.startswith('$'):
                # Check if line uses cdb notation and replace file path with cdb name
                if '<' in line and new_tool_has_cdb:
                    for cdb_name in cdbs:
                        if cdbs[cdb_name].replace('\\','/') in new_tool_file:
                            new_cdb_name = cdb_name
                            new_cdb_loc = cdbs[cdb_name].replace('\\','/')
                            break
                    new_tool_file = new_tool_file.replace(new_cdb_loc, '<' + new_cdb_name + '>')
                fid_newString.write(" Property_File  =  '{}'\n".format(new_tool_file))
                replace = False
                n += 1
            else:
                fid_newString.write(line)

    # Close the string files, delete the original one, and rename the new one
    fid_oldString.close()
    fid_newString.close()
    remove(string_file)
    rename(string_file.replace('.str','.tmp'), string_file)

    return n

def get_string_length(string_file):
    """
    Gets the total length of the drill string defined in string_file
    
    Parameters
    ----------
    string_file :       Full path to an Adams Drill string file
                      
    Returns
    -------
    string_length:      Cumulative length of the string
    
    """
    cdbs = get_adrill_cdbs(os.environ['ADRILL_USER_CFG'], os.environ['ADRILL_SHARED_CFG'])
    # print(cdbs)
    tool_lengths = []
    fid_string = open(string_file, 'r')
    for line in fid_string:
        if ' property_file' in line.lower() and not line.startswith('$'):
            tool_file = line.split("'")[1].replace('/', '\\')
            if '<' in tool_file:
                # Get cdb associated with tool_file
                tool_has_cdb = False
                for cdb_name in cdbs:
                    if '<{}>'.format(cdb_name) in tool_file:
                        tool_cdb_name = cdb_name
                        cdb_loc = cdbs[cdb_name].replace('/','\\')
                        tool_has_cdb = True
                        break  
                # Change cdb notation to full path notation
                if tool_has_cdb:
                    tool_file = tool_file.replace('<{}>'.format(tool_cdb_name), cdb_loc)
                else:
                    raise cdbError('ADrill Database {} not defined.'.format(cdb_name))
            fid_tool = open(tool_file, 'r')
            file_type = ''
            for line in fid_tool:
                if file_type and 'top_drive' not in file_type.lower() and line.replace(' ', '').split('=')[0] in TO_LENGTH_PARAM[file_type] and not line.startswith('$'):
                    tool_length = float(line.replace(' ', '').split('=')[1])
                    tool_lengths.append(tool_length)
                    break
                elif ' file_type' in line.lower() and not line.startswith('$'):
                    file_type = line.replace(' ', '').replace("'",'').replace('\n','').split('=')[1]
            fid_tool.close()
        if ' number_of_joints' in line.lower():
            n = int(line.replace(' ','').split('=')[1])
            tool_lengths[-1] = tool_lengths[-1]*n
    fid_string.close()
    string_length = sum(tool_lengths)
    return string_length

def get_number_of_tools(string_file):
    """
    Gets the total number of tools in a string.  Tools for which quantitiiy can be defined are only counted once.  The top drive is not included

    Parameters
    ----------
    string_file :       Full path to an Adams Drill string file
                      
    Returns
    -------
    num:                Number of tools  
    """
    with open(string_file, 'r') as fid:
        for line in fid:
            if line.lower().startswith(' stack_order '):
                num = int(line.replace(' ','').split('=')[-1])
    
    return num

def get_bha_length(string_file):
    """
    Gets the total length of the drill string defined in string_file NOT including the equivalent upper string and highest most physical string
    
    Parameters
    ----------
    string_file :       Full path to an Adams Drill string file
                      
    Returns
    -------
    string_length:      Cumulative length of the string
    
    """
    cdbs = get_adrill_cdbs(os.environ['ADRILL_USER_CFG'], os.environ['ADRILL_SHARED_CFG'])
    # print(cdbs)
    tool_lengths = []
    with open(string_file, 'r') as fid_string:
        for line in fid_string:
            if ' property_file' in line.lower() and not line.startswith('$'):
                tool_file = line.split("'")[1].replace('/', '\\')
                if '<' in tool_file:
                    # Get cdb associated with tool_file
                    tool_has_cdb = False
                    for cdb_name in cdbs:
                        if '<{}>'.format(cdb_name) in tool_file:
                            tool_cdb_name = cdb_name
                            cdb_loc = cdbs[cdb_name].replace('/','\\')
                            tool_has_cdb = True
                            break  
                    # Change cdb notation to full path notation
                    if tool_has_cdb:
                        tool_file = tool_file.replace('<{}>'.format(tool_cdb_name), cdb_loc)
                    else:
                        raise cdbError('ADrill Database {} not defined.'.format(cdb_name))
                fid_tool = open(tool_file, 'r')
                file_type = ''
                for line in fid_tool:
                    if file_type and 'top_drive' not in file_type.lower() and line.replace(' ', '').split('=')[0] in TO_LENGTH_PARAM[file_type] and not line.startswith('$'):
                        tool_length = float(line.replace(' ', '').split('=')[1])
                        tool_lengths.append(tool_length)
                        break
                    elif ' file_type' in line.lower() and not line.startswith('$'):
                        file_type = line.lower().replace(' ', '').replace("'",'').replace('\n','').split('=')[1]
                fid_tool.close()
            if ' number_of_joints' in line.lower():
                n = int(line.replace(' ','').split('=')[1])
                tool_lengths[-1] = tool_lengths[-1]*n
    string_length = sum(tool_lengths[:-2])
    return string_length
    
def add_cdb_to_cfg(name, loc, cfg_file):
    """Adds cdb of name 'name' and path 'loc' to cfg_file
    
    Arguments:
        name {string} -- name of cdb (e.g. example_database)
        loc {string} -- path to cdb (e.g. C:\\example_database.cdb)
        cfg_file {string} -- Full filename of an adams drill configuration file
    
    Raises:
        ValueError -- Raised if a cdb of the given name or path already exists in the given config file
        PermissionError -- Raised if the user does not have permissiosn to edit the given config file
    """

    loc = os.path.normpath(loc)
    cdbs = {}

    # Read config file
    with open(cfg_file, 'r') as fid:
        lines = fid.readlines()

    # Pull cdbs from config file into a dictionary
    for line in lines:
        if line.lower().startswith('database'):
            splt = re.split('[ \t]+', line.replace('\n',''), maxsplit=2)
            cdbs[splt[1]] = os.path.normpath(splt[2])
    
    # Check if cdb name already exists
    if name in cdbs:
        raise ValueError('{} already exists in {}.'.format(name, cfg_file))
    
    # Check if cdb location already exists
    for cdb_name in cdbs:
        if loc is cdbs[cdb_name]:
            raise ValueError('{} already exists in {}'.format(loc, cfg_file))
    
    # Add new cdb to cdbs dictionary
    cdbs[name] = loc

    # Rewrite config file with new cdb
    try:
        with open(cfg_file, 'w') as fid:
            cdbs_written = False
            for line in lines:
                if not line.lower().startswith('database'):
                    fid.write(line)
                elif not cdbs_written:
                    for cdb_name, cdb_loc in cdbs.items():
                        text = 'DATABASE   {}   {}\n'.format(cdb_name, cdb_loc)
                        fid.write(text)
                    cdbs_written = True
    except PermissionError:
        raise PermissionError('You do not have permission to edit {}.'.format(cfg_file))    

def remove_cdb_from_cfg(name, cfg_file):
    """Removes cdb of name 'name' from cfg_file
    
    ==========
    Arguments:
    ==========
        name {string} -- name of cdb (e.g. example_database)
        cfg_file {string} -- Full filename of an adams drill configuration file
    
    ==========
    Raises:
    ==========
        ValueError -- Raised if a cdb of the given name or path already exists in the given config file
        PermissionError -- Raised if the user does not have permissiosn to edit the given config file
    """

    # Initialize cdbs dictionary
    cdbs = {}

    # Read config file
    with open(cfg_file, 'r') as fid:
        lines = fid.readlines()

    # Pull cdbs from config file into a dictionary
    for line in lines:
        if line.lower().startswith('database'):
            splt = re.split('[ \t]+', line.replace('\n',''), maxsplit=2)
            cdbs[splt[1]] = os.path.normpath(splt[2])
    
    # Check if cdb name exists
    if name not in cdbs:
        raise ValueError('{} does not exist in {}.'.format(name, cfg_file))
    
    # Remove cdb from cdbs dictionary
    del cdbs[name]

    # Rewrite config file with the cdb removed
    try:
        with open(cfg_file, 'w') as fid:
            cdbs_written = False
            for line in lines:
                if not line.lower().startswith('database'):
                    fid.write(line)
                elif not cdbs_written:
                    for cdb_name, cdb_loc in cdbs.items():
                        text = 'DATABASE   {}   {}\n'.format(cdb_name, cdb_loc)
                        fid.write(text)
                    cdbs_written = True
    except PermissionError:
        raise PermissionError('You do not have permission to edit {}.'.format(cfg_file))  

def create_cfg_file(filename, database_paths):
    """Create a cfg file with the databases whose paths are given in the database_paths list.
    Also sets the ADRILL_USER_CONFIG environment variable equal to filename.
    
    Arguments:
        filename {string} -- Filename for the new configuration file.
        database_paths {list} -- List of database paths to include in the configuration file. 
    """


    # Create a databases dictionary
    databases = []    
    for path in database_paths:
        name = os.path.split(path)[1].replace('.cdb','')
        databases.append({'name': name, 'path': path})

    # Get the cfg template
    cfg_template = env.get_template('template.cfg')
    
    # Write the new cfg file
    with open(filename ,'w') as fid:
        fid.write(cfg_template.render(databases=databases))
    
    os.environ['ADRILL_USER_CFG'] = os.path.join(os.getcwd(), filename)

def build(string, solver_settings, working_directory, output_name=None):    
    """Builds adm, acf, and cmd files from string, event, and solver settings files.
    
    Arguments:
        string {DrillString} -- adripy.tiem_orbit.DrillString object
        solver_settings {DrillSolverSettings} -- adripy.tiem_orbit.DrillSolverSettings object
        working_directory {string} -- Path to the directory to put the adm, acf, and cmd.
    
    Keyword Arguments:
        output_name {string} -- Base name of the adm, acf, and cmd files. (default: Same as string_file)
    """
    # Create a DrillString object
    string_file = string.write_to_file(directory=working_directory, publish=True)
    
    # Set the output name
    if output_name is None:
        output_name = string.parameters['OutputName']
    else:
        string.rename(output_name, remove_original=True)
        
    # Write a solver settings file to the working directory
    solver_settings.write_to_file(write_directory=working_directory)    

    # Set the names of the output files
    adm_file = output_name + '.adm'
    print(adm_file)
    acf_file = output_name + '.acf'
    cmd_file = output_name + '.cmd'
    
    # Format the string filename
    adams_formatted_str_filename = os.path.normpath(get_full_path(string_file)).replace(os.sep, '/')
    
    # Set the event filename and solver settings file name (relative paths)
    evt_name = os.path.split(string.parameters['Event_Property_File'])
    ssf_name = os.path.split(solver_settings.filename)

    # Create aview script
    cmds = []    
    cmds.append(f'ds TOStart string_cfg_file = "{adams_formatted_str_filename}"\n')
    cmds.append(f'adrill build acf ssf="{ssf_name}" evt="{evt_name}"\n')
    cmds.append(f'file adams write file="{adm_file}"\n')
    cmds.append(f'simulation script write_acf sim_script_name = "{output_name}" file_name = "{acf_file}"\n')
    cmds.append(f'file command write entity_name = "{output_name}" file_name = "{cmd_file}"')
    with open(os.path.join(working_directory, 'build.cmd'), 'w') as fid:			
        for cmd in cmds:
            fid.write(cmd)
                                            
    # Run adams to generate adm, acf, cmd
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    process = subprocess.Popen('{} aview ru-s b build.cmd'.format(os.environ['ADAMS_LAUNCH_COMMAND']), cwd=working_directory, startupinfo=startupinfo)
    process.wait()            

class cdbError(Exception):
    pass
