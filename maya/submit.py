import os
import subprocess
import pymel.core as pm
from pymel import versions
import pprint

default_priority = '5000'
default_threads  = '16'
default_allcores = False
default_chunk    = '1'
default_maxcpu   = '183'

class RenderSubmitWindow(pm.uitypes.Window):

    def __init__(self, *a):
        try: pass
            #pm.deleteUI(jobtype)
        except: pass
        jobtype = 'mayacmd'
        self.submit_dict = self.getSceneData(jobtype)

        self.default_name = pm.sceneName().basename().rstrip('.mb')

        #################################################################################
        ## UI LAYOUT
        #################################################################################
        
        self.setTitle('Submit Scene to Qube')
        self.setToolbox()
        #self.setResizeToFitChildren(1)
        self.setSizeable(0)

        main_layout = pm.formLayout(p=self)

        # input / output paths
        column = pm.formLayout(p=main_layout)


        self.job_text = pm.textFieldGrp(
            'job_text',
            label='Job Name', 
            text=self.submit_dict['name'], 
            cc=self.setName, 
            tcc=self.setName,
            p=column,
            cw2=(110,655)
            )
        self.scene_text = pm.textFieldGrp(
            'scene_text',
            label='Scene File', 
            text=self.submit_dict['package']['scenefile'], 
            cc=self.setScenePath, 
            tcc=self.setScenePath,
            p=column,
            cw2=(110,655)
            )
        self.project_text = pm.textFieldGrp(
            'project_text',
            label='Project Path', 
            text=self.submit_dict['package']['-proj'],
            ed=False,
            p=column,
            cw2=(110,655)
            )
        self.outdir_text = pm.textFieldGrp(
            'outdir_text',
            label='Render Path (optional)', 
            text='',
            cc=self.setRenderPath,
            p=column,
            cw2=(110,655)
            )
        column.redistribute()

        # 2 columns
        column = pm.formLayout(p=main_layout)
        column.flip()
        rows = pm.formLayout(p=column)
       
        # frame range
        self.frange_text = pm.textFieldGrp(
            'frange_text',
            l='Frame Range', 
            text=self.submit_dict['package']['range'], 
            cc=self.setRange,
            tcc=self.setRange,
            cw2=(110, 80), 
            p=rows
            )
        self.chunk_text = pm.textFieldGrp(
            'chunk_text',
            l='Chunk Size',
            text=default_chunk,
            cc=self.setChunk,
            tcc=self.setChunk,
            cw2=(110, 80),
            p=rows
            )

        # num. threads
        threads_col = pm.rowLayout(p=rows, nc=2)
        self.threads_text = pm.textFieldGrp(
            'threads_text',
            l='Num. Threads',
            text=default_threads,
            tcc=self.setThreads,
            cw2=(110, 40),
            p=threads_col
            )
        self.threads_text.setEnable(1)

        self.threads_chkbox = pm.checkBox(
            'threads_chkbox',
            l='All',
            value=default_allcores,
            cc=self.setThreads,
            p=threads_col
            )

        # priority
        self.priority_text = pm.textFieldGrp(
            'priority_text',
            l='Priority', 
            text=default_priority, 
            cc=self.setPriority,
            tcc=self.setPriority,
            cw2=(110, 80),
            p=rows)

        # cluster
        cluster_col = pm.rowLayout(p=rows, nc=2)
        self.cluster_text = pm.textFieldGrp(
            'cluster_text',
            l='Cluster', 
            text='/',
            cc=self.setCluster,
            tcc=self.setCluster,
            cw2=(110, 40), 
            p=cluster_col
            )
        self.restrict_chkbox = pm.checkBox(
            'restrict_chkbox',
            l='Restrict?',
            value=False,
            cc=self.setCluster,
            p=cluster_col
            )
        self.restrict_text = pm.textFieldGrp(
            'restrict_text',
            l='Restrict to Clusters',
            text='',
            cc=self.setCluster,
            tcc=self.setCluster,
            cw2=(110, 80),
            enable=False,
            p=rows
            )
        rows.redistribute()

        rows = pm.formLayout(p=column)
        self.submit_btn = pm.button(label='Submit Current Layer', height=10, c=self.submit, p=rows)
        self.submit_all_btn = pm.button(label='Submit All Renderable Layers', height=10, c=self.submit_all, p=rows)
        rows.redistribute()       
 
        column.redistribute(1,2)

        main_layout.redistribute(1,1.5)

        self.setThreads()

    ### UI FUNCTIONS
    def refresh(self, jobtype, *a):
        ''' Resets the submit_dict based on jobtype, and populates it with current UI values. '''
        self.submit_dict = getSceneData(jobtype)
        self.setChunk(jobtype)
        self.setName()
        self.setPriority()
        self.setScenePath()
        self.setRenderPath(jobtype)
        self.setRange()
        self.setCluster()
        self.setThreads()
        self.setVersion(jobtype)

    def setChunk(self, jobtype, *a):
        #if jobtype == 'mayacmd':
        self.chunk_text.setEnable(True)
        new = self.chunk_text.getText()
        self.submit_dict['package']['rangeExecution'] = 'chunks:' + str(new)
        self.submit_dict['package']['rangeChunkSize'] = str(new)
        #elif jobtype == 'mayapy':
        #    self.chunk_text.setEnable(False)
        #    self.submit_dict['package'].pop('rangeExecution', None)
        #    self.submit_dict['package'].pop('rangeChunkSize', None)
        return

    def setName(self, *a):
        new = self.job_text.getText()
        self.submit_dict['name'] = new
        return

    def setPriority(self, *a):
        new = self.priority_text.getText()
        self.submit_dict['priority'] = new
        return

    def setScenePath(self, *a):
        new = self.scene_text.getText()
        self.submit_dict['package']['scenefile'] = new
        return

    def setRenderPath(self, jobtype, *a):
        new = self.outdir_text.getText()
        if jobtype == 'mayacmd':
            self.submit_dict['package']['-rd'] = new
        elif jobtype == 'mayapy':
            self.submit_dict['package']['renderDirectory'] = new
        pass

    def setRange(self, *a):
        new = self.frange_text.getText()
        self.submit_dict['package']['range'] = new
        return

    def setCluster(self, *a):
        # query the checkbox
        box_checked  = self.restrict_chkbox.getValue()
        cluster      = self.cluster_text.getText()
        restrictions = self.restrict_text.getText()

        self.submit_dict['cluster'] = cluster

        if box_checked:
            self.restrict_text.setEnable(1)
            self.submit_dict['restrictions'] = restrictions

        elif not box_checked:
            self.restrict_text.setEnable(0)
            self.submit_dict['restrictions'] = ''
        return

    def setThreads(self, *a):
        # query the checkbox
        box_checked = self.threads_chkbox.getValue()

        # if checked, ignore the text box, set threads to all
        if box_checked:
            self.threads_text.setEnable(0)
            self.submit_dict['package']['renderThreads'] = 0
            self.submit_dict['package']['renderThreadCount'] = 1
            self.submit_dict['reservations'] = 'host.processors=1+'
            self.submit_dict['requirements'] = 'host.processors.used==0'

        # if unchecked, query the text field
        if not box_checked:
            self.threads_text.setEnable(1)
            threads = self.threads_text.getText()
            self.submit_dict['reservations'] = 'host.processors=' + str(threads)
            self.submit_dict['package']['renderThreads'] = int(threads)
            self.submit_dict['package']['renderThreadCount'] = int(threads)
            self.submit_dict['requirements'] = ''
        return

    def setVersion(self, jobtype, *a):
        if jobtype == 'mayacmd':
            if versions.current()/100 == 2013:
                return "R:\\Program Files\\Autodesk\\Maya2013\\bin\\Render.exe"
            if versions.current()/100 == 2015:
                return "R:\\Program Files\\Autodesk\\Maya2015\\bin\\Render.exe"
        #elif jobtype == 'mayapy':
        #    if versions.current()/100 == 2013:
        #        return "R:\\Program Files\\Autodesk\\Maya2013\\bin\\mayabatch.exe"
        #    if versions.current()/100 == 2015:
        #        return "R:\\Program Files\\Autodesk\\Maya2015\\bin\\mayabatch.exe"

    def getSceneData( self, jobtype, *a ):
        """Gathers scene information and executes the shell command to open a Qube submission window"""
        rg = pm.PyNode('defaultRenderGlobals')

        scene_file_path = pathFormat(pm.system.sceneName())
        project_path    = pathFormat(pm.workspace(q=True, rd=True).replace('/','\\'))
        image_path      = pathFormat(os.path.join(project_path, pm.workspace('images', q=True, fre=True)).replace('/','\\'))
        frame_range     = str(int(rg.startFrame.get())) + "-" + str(int(rg.endFrame.get()))
        scene_cameras   = ','.join(getSceneUserCameras())
        renderer        = rg.ren.get()
        render_layers   = ','.join([str(layer) for layer in pm.ls(type='renderLayer') if not 'defaultRenderLayer' in str(layer)])
        layer_name      = str(pm.editRenderLayerGlobals(q=True, crl=True))
        render_exe      = self.setVersion(jobtype)

        submit_dict = {
            'name': 'maya(cmd) ' + pm.sceneName().basename().rstrip('.mb'),
            'prototype':'cmdrange',
            'package':{
                'simpleCmdType': 'Maya BatchRender (vray)',
                'scenefile': scene_file_path,
                '-proj': project_path, 
                '-cam' : scene_cameras,
                'range': frame_range,
                '-rl': layer_name,
                '-rd': '',
                '-threads' : default_threads,
                'renderThreads': default_threads,
                'mayaExe': render_exe,
                'rangeExecution': 'chunks:' + str(default_chunk),
                'rangeChunkSize': str(default_chunk)
                },
            'cluster': '/',
            'restrictions': '',
            'requirements': '',
            'priority': default_priority,
            'cpus': default_maxcpu,
            'reservations': 'host.processors=' + str(default_threads),
            'flagsstring': 'auto_wrangling,disable_windows_job_object'
            }
        '''
        submit_dict_mayapy = {
            'name': 'maya(py) ' + pm.sceneName().basename().rstrip('.mb'),
            'prototype':'maya',
            'package':{
                'scenefile': scene_file_path.replace('/','\\'),
                'project': project_path, 
                'range': frame_range, 
                'cameras_all': scene_cameras, 
                'layers_all': render_layers,
                'layers': layer_name,
                'mayaExecutable': render_exe,
                'renderDirectory': image_path,
                'renderThreads': default_threads,
                'renderThreadCount': default_threads,
                'ignoreRenderTimeErrors': True
                },
         'cluster': '/',
         'restrictions': '',
         'requirements': '',
         'priority': default_priority,
         'cpus': default_maxcpu,
         'reservations': 'host.processors=' + str(default_threads),
         'flagsstring': 'auto_wrangling,disable_windows_job_object'
        }

        # SANITY CHECKS
        # 1- scene never saved
        if scene_file_path == '':
            pm.confirmDialog( title='Scene not saved.',
                              button='Whoops',
                              message='Please save scene on cagenas before submitting.',
                              defaultButton='Whoops'
                              )
            return 'sanity check fail'

        # 2- no user cameras in scene
        if scene_cameras == None:
            pm.confirmDialog( title='No renderable camera.',
                              button='Whoops',
                              message='No renderable cameras found in your scene.',
                              defaultButton='Whoops'
                              )
            return 'sanity check fail'

        elif len(scene_cameras) > 1:
            confirm = pm.confirmDialog( title='Multiple renderable cameras.',
                              button=('Whoops', 'That\'s fine'),
                              cancelButton='That\'s fine',
                              message='You have multiple renderable cameras in your scene.  All of them will be rendered.  Proceed?',
                              defaultButton='Whoops',
                              dismissString='That\'s fine'
                              )
            if confirm == 'That\'s fine':
                pass
            elif confirm == 'Whoops':
                return 'sanity check fail'

        # 3- animation rendering not enabled
        if rg.animation.get() == False:
            check = pm.confirmDialog( title='Animation not enabled.',
                                      button=('Whoops', 'That\'s fine'),
                                      cancelButton='That\'s fine',
                                      message='Animation is not enabled in your render globals.',
                                      defaultButton='Whoops',
                                      dismissString='That\'s fine'
                                      )
            print check
            if check == 'Whoops':
                return 'sanity check fail'
            else: pass

        # 4- framerate weirdness
        if (rg.endFrame.get() % int(rg.endFrame.get())):
            pm.confirmDialog( title='Framge range is strange!',
                              button='Whoops',
                              message='Animation frame range is wonky.  Did you change framerate?',
                              defaultButton='Whoops'
                              )
            return 'sanity check fail'        
        '''
        if jobtype == 'mayacmd':
            return submit_dict
        elif jobtype == 'mayapy':
            return submit_dict_mayapy


    def run(self):
        self.show()

    def submit( self, qube_gui=1, *a ):
        """ Runs the Qube submission console command for the current render layer. """

        layer = pm.editRenderLayerGlobals(q=True, crl=True)
        self.submit_dict['package']['-rl'] = str(layer)
        self.submit_dict['name'] = pm.sceneName().basename().rstrip('.mb') + ' : ' + str(layer)

        #if qube_gui:
        subprocess.Popen(['c:\\program files (x86)\\pfx\\qube\\bin\\qube-console.exe', '--submitDict', str(self.submit_dict)])
        #else:
        #    subprocess.Popen(['c:\\program files (x86)\\pfx\\qube\\bin\\qube-console.exe', '--nogui', '--submitDict', str(self.submit_dict)])

    def submit_all(self, *a):
        """ Iterates over all active render layers and submits each one individually. """

        render_layers = [layer for layer in pm.ls(type='renderLayer') if (not 'defaultRenderLayer' in str(layer)) and layer.renderable.get()]

        for layer in render_layers:
            pm.editRenderLayerGlobals(crl=layer)
            self.submit()


    def __test(self, *a):
        layer = pm.editRenderLayerGlobals(q=True, crl=True)
        self.submit_dict['package']['-rl'] = str(layer)
        self.submit_dict['name'] = pm.sceneName().basename().rstrip('.mb') + ' : ' + str(layer)

        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self.submit_dict)
        return


def getSceneUserCameras( *a ):
    """Returns a list of all non-default cameras in the scene """
    default_cameras = ['topShape', 'sideShape', 'frontShape', 'perspShape']
    cams = [str(cam) for cam in pm.ls(typ='camera') if cam not in default_cameras and cam.renderable.get()]
    if len(cams) > 0:
        return cams
    else: return []


def pathFormat( path ):
    """ Force updates drive mapping to unc paths """
    path = path.replace('\\','/')
    return str(path.replace('Y:/','//cagenas/'))


def listToStr( list_obj ):
    """ Converts a list of objects to a space-separated string of object names """

    if 'str' in str(list_obj.__class__):
        return list_obj
    elif not 'list' in str(list_obj.__class__):
        pm.error('Unexpected object type ' + str(list_obj.__class__) + ' in _listToStr.')
        return None

    out_str = ""

    for i in range(len(list_obj)):
        # if it is the only or last element in the list
        if (i+1) == len(list_obj):
            out_str += str(list_obj[i])
        # if it is the 1 to (n-1) element of the list
        elif (i+1) < len(list_obj):
            out_str = out_str + str(list_obj[i]) + " "        
        else: return '#EMPTY_LIST'
    return out_str


def run(*a):
    submission = RenderSubmitWindow()
    submission.run()
    return
