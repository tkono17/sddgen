#------------------------------------------------------------------------
# sddgen: generator.py
#------------------------------------------------------------------------
import re
import logging

logger = logging.getLogger(__name__)

class Generator:
    def __init__(self, name='', model=None, output='sddout'):
        self.name = name
        self.data = model
        #
        self.header = None
        self.document = None
        self.components = None
        self.styles = None
        if self.data:
            self.header = self.data.header
            self.document = self.data.document
            self.components = self.data.components
            self.styles = self.data.styles
        self.outputName = output
        #
        
    def findStyleFor(self, ctype):
        x = None
        if self.styles:
            logging.debug('Styles are there')
            if ctype in self.styles.keys():
                logging.debug('  Style for %s found' % ctype)
                x = self.configuration[ctype]
            else:
                logging.debug('  Style for %s cannot be found' % ctype)
        else:
            logging.debug('  Style is empty')
        return x

    def findComponent(self, typeName):
        component = None
        return component
    
    def writeDocument(self, fout):
        pass
    
    def writeEntry(self, fout):
        pass
    
    def writeStyles(self, fout):
        pass
    
    def writeStyle(self, fout):
        pass
    
    def generate(self):
        cname = self.__class__.__name__
        logger.warning('Cannot generate output for %s' % cname)
        pass

    pass

class TkGenerator(Generator):
    def __init__(self, data):
        super().__init__(name='TkGenerator', data=data)

    def generate(self, fn_out):
        prefix=''
        dashes = '-'*70
        with open(fn_out, 'w') as fout:
            fout.write('#%s\n' % dashes)
            fout.write('# Generated by ssdgen.py from %s\n' % self.filenameIn)
            fout.write('#%s\n' % dashes)
            fout.write('import tkinter as tk\n')
            fout.write('from tkinter import ttk\n')
            fout.write('\n')
            self.outputComponent(self.documentKey, self.document, fout, prefix)
            for compKey, comp in self.components.items():
                compName, tags = self.decodeKey(compKey)
                baseName = ''
                if len(tags)>0: baseName = tags[0]
                fout.write('\n')
                fout.write('# Component: %s\n' % compName)
                self.outputComponent(compKey, comp, fout, prefix)
        pass

    def outputPlacement(self, name, data, fout, prefix):
        logger.debug('Write out placement of %s' % name)
        if data != None:
            if 'pack' in data.keys():
                pack = data['pack']
                s = prefix + '%s.pack(' % name
                opts = ('side', 'anchor', 'fill', 'expand')
                for opt in opts:
                    if opt in pack.keys():
                        s += '%s=%s, ' % (opt, pack[opt])
                s = s.rstrip(' ').rstrip(',')
                fout.write('%s)\n' % s)
            elif 'grid' in data.keys():
                pass
            elif 'place' in data.keys():
                pass
            else:
                logging.warning('No placement for %s' % name)
        else:
            logging.warning('No style for %s' % name)

    def optionsString(self, style):
        opts=''
        excludeKeys = ('pack', 'grid', 'place')
        if style and len(style.keys())>0:
            for key in style.keys():
                if key in excludeKeys: continue
                opt = '%s=%s' % (key, style[key])
                opts += ', %s' % opt
        return opts
    
    def outputObjectCreation(self, parentName, key, data, fout, prefix):
        name, tags = self.decodeKey(key)
        clsName = tags[0]
        compName = ','.join(tags)
        style = self.findConfigurationFor(compName)
        opts = self.optionsString(style)
        #
        placeIt = True
        if compName == 'tk.Menu,bar':
            fout.write(prefix+'%s = %s(%s%s)\n' % (name, clsName, parentName, opts) )
            fout.write(prefix+'self.root.config(menu=%s)\n' % name)
            placeIt = False
        elif compName == 'tk.Menu,cascade':
            fout.write(prefix+'%s = %s(%s%s)\n' % (name, clsName, parentName, opts) )
            fout.write(prefix+'%s.add_cascade(label="%s", menu=%s)\n' % (parentName, name, name))
            pass
            placeIt = False
        elif compName == 'tk.Menu':
            if data == 'command':
                fout.write(prefix+'%s.add_command(label="%s")\n' % (parentName, name))
            elif data == 'checkbutton':
                fout.write(prefix+'%s.add_checkbutton(label="%s")\n' % (parentName, name))
            elif data == 'radiobutton':
                fout.write(prefix+'%s.add_radiobutton(label="%s")\n' % (parentName, name))
            placeIt = False
        elif clsName == 'ttk.Label':
            label = name
            if data: label = data
            fout.write(prefix+'%s = %s(%s, text="%s"%s)\n' %\
                       (name, clsName, parentName, label, opts) )
        elif clsName == 'ttk.Button':
            label = name
            if data: label = data
            fout.write(prefix+'%s = %s(%s, text="%s"%s)\n' %\
                       (name, clsName, parentName, label, opts) )
        else:
            fout.write(prefix+'%s = %s(%s%s)\n' % (name, clsName, parentName, opts) )
        if placeIt:
            if style:
                self.outputPlacement(name, style, fout, prefix)
            else:
                logger.warning('No style for %s, use pack(fill=tk.BOTH, expand=True)' % name)
                style1 = { 'pack': { 'fill': 'tk.BOTH', 'expand': 'True' } }
                self.outputPlacement(name, style1, fout, prefix)
        pass

    def outputSubComponent(self, parentName, key, data, fout, prefix=''):
        name, tags = self.decodeKey(key)
        clsName = tags[0]
        compName = ','.join(tags)
        style = self.findConfigurationFor(compName)
        #
        self.outputObjectCreation(parentName, key, data, fout, prefix)
        #
        keys = self.keys(data)
        for key1 in keys:
            name1, tags1 = self.decodeKey(key1)
            if len(tags1)==0:
                logger.warning('No class name give in tags for %s' % name)
                continue
            clsName1 = tags1[0]
            data1 = self.child(data, key1)
            fout.write('\n')
            self.outputSubComponent(name, key1, data1, fout, prefix)
        #
        logger.info(clsName)
        if clsName == 'ttk.PanedWindow':
            fout.write('\n')
            for key1 in keys:
                name1, tags1 = self.decodeKey(key1)
                fout.write(prefix+'%s.add(%s)\n'% (name, name1))
        pass
    
    def outputComponent(self, key, data, fout, prefix=''):
        name, tags = self.decodeKey(key)
        clsName = tags[0]
        fout.write(prefix+'class %s(%s):\n' % (name, clsName))
        fout.write(prefix+'    def __init__(self, parent):\n')
        fout.write(prefix+'        super().__init__(parent)\n')
        fout.write(prefix+'        self.root = parent\n')
        fout.write(prefix+'        self.pack(fill=tk.BOTH, expand=True)\n')
        fout.write(prefix+'        self.buildGui()\n')
        fout.write(prefix+'\n')
        fout.write(prefix+'    def buildGui(self):\n')
        keys = self.keys(data)
        for key1 in keys:
            name1, tags1 = self.decodeKey(key1)
            if len(tags1)==0:
                logger.warning('No class name give in tags for %s' % name)
                continue
            clsName1 = tags1[0]
            data1 = self.child(data, key1)
            prefix2 = prefix + '        '
            self.outputSubComponent('self', key1, data1, fout, prefix2)
            fout.write('\n')
        fout.write(prefix+'        pass\n')
        fout.write(prefix+'    pass\n')
    pass
