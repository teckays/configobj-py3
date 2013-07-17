# configobj_test.py
# doctests for ConfigObj
# A config file reader/writer that supports nested sections in config files.
# Copyright (C) 2005-2010 Michael Foord, Nicola Larosa
# E-mail: fuzzyman AT voidspace DOT org DOT uk
#         nico AT tekNico DOT net

# ConfigObj 4
# http://www.voidspace.org.uk/python/configobj.html

# Released subject to the BSD License
# Please see http://www.voidspace.org.uk/python/license.shtml

# Scripts maintained at http://www.voidspace.org.uk/python/index.shtml
# For information about bugfixes, updates and support, please join the
# ConfigObj mailing list:
# http://lists.sourceforge.net/lists/listinfo/configobj-develop
# Comments, suggestions and bug reports welcome.


from io import StringIO

import os
import sys

if sys.version_info <= (2,2):
    raise RuntimeError("Python v.2.2 or later needed")

try:
    import unittest2 as unittest
except ImportError:
    import unittest

try:
    from codecs import BOM_UTF8
except ImportError:
    BOM_UTF8 = '\xef\xbb\xbf'
    
from configobj import *
from validate import Validator, VdtValueTooSmallError

# Test helper methods

def raiseError(err, arg=None):
    if arg:
        raise err(arg)
    else:
        raise err

def transform(section, key):
    val = section[key]
    newkey = key.replace('XXXX', 'CLIENT1')
    section.rename(key, newkey)
    if isinstance(val, (tuple, list, dict)):
        pass
    else:
        val = val.replace('XXXX', 'CLIENT1')
        section[newkey] = val
        
# Unittests

class TestConfigObj(unittest.TestCase):
    def test_basic_functionality(self):
        z = ConfigObj()
        z['a'] = 'a'
        z['sect'] = { 'subsect': 
                        {   'a': 'fish',
                            'b': 'wobble',
                        },
                       'member': 'value'
                    }
        x = ConfigObj(z.write())
        self.assertEquals(z, x)
    
    def test_error_classes(self):
        self.assertRaises(ConfigObjError, raiseError, ConfigObjError)
        self.assertRaises(NestingError, raiseError, NestingError)        
        self.assertRaises(ParseError, raiseError, ParseError)        
        self.assertRaises(DuplicateError, raiseError, DuplicateError)
        self.assertRaises(ConfigspecError, raiseError, ConfigspecError)        
        self.assertRaises(ConfigObjError, raiseError, ConfigObjError)
        self.assertRaises(InterpolationLoopError, raiseError, InterpolationLoopError, "yoda")
        self.assertRaises(RepeatSectionError, raiseError, RepeatSectionError)
        self.assertRaises(MissingInterpolationOption, raiseError, MissingInterpolationOption, "yoda")
        self.assertRaises(ReloadError, raiseError, ReloadError)
        
    def test_section_methods(self):
        a = '''
[section1]
option1 = True
[[subsection]]
more_options = False
# end of file
'''
        a = a.splitlines()
        b = '''
# File is user.ini
[section1]
option1 = False
# end of file'''
        b = b.splitlines()
        c1 = ConfigObj(b)
        c2 = ConfigObj(a)
        c2.merge(c1)
        x = ConfigObj({'section1': 
                    {'option1': 'False', 'subsection': 
                        {'more_options':  'False'}
                    }
                  })
        
        self.assertEquals(c2, x)
        
        config = '''
[XXXXsection]
XXXXkey = XXXXvalue
'''.splitlines()
        cfg = ConfigObj(config)
        self.assertEquals(cfg, ConfigObj({'XXXXsection': {'XXXXkey': 
                'XXXXvalue'}}))
                
        self.assertEquals(cfg.walk(transform, call_on_sections=True),
        {'CLIENT1section': {'CLIENT1key': None}})
        
        self.assertEquals(cfg, ConfigObj({'CLIENT1section': 
                            {'CLIENT1key': 'CLIENT1value'}}))
                            
    def test_reset(self):
        something = object()
        c = ConfigObj()
        c['something'] = something
        c['section'] = {"something": something}
        c.filename = "fish"
        c.raise_errors = something
        c.list_values = something
        c.create_empty = something
        c.file_error = something
        c.stringify = something
        c.indent_type = something
        c.encoding = something
        c.default_encoding = something
        c.BOM = something
        c.newlines = something
        c.write_empty_values = something
        c.unrepr = something
        c.initial_comment = something
        c.final_comment = something
        c.configspec = something
        c.inline_comments = something
        c.comments = something
        c.defaults = something
        c.reset()
        
        self.assertFalse(c.raise_errors)
        self.assertTrue(c.list_values)
        self.assertFalse(c.create_empty)
        self.assertTrue(c.interpolation)        
        self.assertTrue(c.stringify)
        self.assertFalse(c.unrepr)
        self.assertFalse(c.write_empty_values)
        self.assertFalse(c.inline_comments)
        self.assertFalse(c.comments)
        self.assertFalse(c.defaults)
        self.assertFalse(c.default_values)
        self.assertEquals(c, ConfigObj())
        self.assertEquals(c, ConfigObj({}))
        
    def test_configobj(self):
        c = '''
        [hello]
        member = value
        [hello again]
        member = value
        [ "hello" ]
        member = value
        '''
        self.assertRaises(DuplicateError, ConfigObj, c.split('\n'), raise_errors=True)
        
        d = '''
        [hello]
        member = value
        [hello again]
        member1 = value
        member2 = value
        'member1' = value
        [ "and again" ]
        member = value
        '''
        self.assertRaises(DuplicateError, ConfigObj, c.split('\n'), raise_errors=True)
        
        c = ConfigObj()
        c['DEFAULT'] = {
            'b': 'goodbye',
            'usedir': 'c:\\\\home',
            'c': '%(d)s',
            'd': '%(c)s'
            }
        c['section'] = {
                'a': '%(datadir)s\\\\some path\\\\file.py',
                'b': '%(userdir)s\\\\some path\\\\file.py',
                'c': 'Yo %(a)s',
                'd': '%(not_here)s',
                'e': '%(e)s',
            }
        c['section']['DEFAULT'] = {
                'datadir': 'c:\\\\silly_test',
                'a': 'hello - %(b)s',
            }
                
        self.assertEquals(c['section']['a'], 
                'c:\\\\silly_test\\\\some path\\\\file.py')
        self.assertEquals(c['section']['c'], 
                'Yo c:\\\\silly_test\\\\some path\\\\file.py')
        
        # Switching interpolation off.
        c.interpolation = False

        self.assertEquals(c['section']['a'], 
                '%(datadir)s\\\\some path\\\\file.py')
        self.assertEquals(c['section']['b'], 
                '%(userdir)s\\\\some path\\\\file.py')
        self.assertEquals(c['section']['c'], 
                'Yo %(a)s')
                
        # Testing interpolation errors
        c.interpolation = True
    
        def dummyErrorRaiser():
            c['section']['d']
        self.assertRaises(MissingInterpolationOption, 
                            dummyErrorRaiser)
        
        def dummyErrorRaiser():
            c['section']['e']
        self.assertRaises(InterpolationLoopError, 
                            dummyErrorRaiser)
                            
        interp_cfg = '''
        [DEFAULT]
        keyword1 = value1
        'keyword 2' = 'value 2'
        reference = ${keyword1}
        foo = 123
        [ section ]
        templatebare = $keyword1/foo
        bar = $$foo
        dollar = $$300.00
        stophere = $$notinterpolated
        with_braces = ${keyword1}s (plural)
        with_spaces = ${keyword 2}!!!
        with_several = $keyword1/$reference/$keyword1
        configparsersample = %(keyword 2)sconfig
        deep = ${reference}    
        [[DEFAULT]]
        baz = $foo
        [[ sub-section ]]
        quux = '$baz + $bar + $foo'    
            [[[ sub-sub-section ]]]
            convoluted = "$bar + $baz + $quux + $bar"
        '''
        c = ConfigObj(interp_cfg.split('\n'), 
                    interpolation='Template')
        self.assertEquals(c['section']['templatebare'],
                    'value1/foo')
        
        self.assertEquals(c['section']['dollar'], 
                    '$300.00')
                    
        self.assertEquals(c['section']['stophere'], 
                    '$notinterpolated')
                    
        self.assertEquals(c['section']['with_braces'], 
                    'value1s (plural)')

        self.assertEquals(c['section']['with_spaces'], 
                    'value 2!!!')
                    
        self.assertEquals(c['section']['with_several'], 
                    'value1/value1/value1')

        self.assertEquals(c['section']['configparsersample'], 
                    '%(keyword 2)sconfig')

        self.assertEquals(c['section']['deep'], 
                    'value1')

        self.assertEquals(c['section']['sub-section']['quux'], 
                    '123 + $foo + 123')
                    
        self.assertEquals(c['section']['sub-section']
                           ['sub-sub-section']['convoluted'],    
                   '$foo + 123 + 123 + $foo + 123 + $foo')

        c.stringify = False
        def dummyErrorRaiser():
            c['test'] = 1
        self.assertRaises(TypeError, dummyErrorRaiser)

        cfg_with_empty = '''
        k =
        k2 =# comment test
        val = test
        val2 = ,
        val3 = 1,
        val4 = 1, 2
        val5 = 1, 2,
        '''.splitlines()
        cwe = ConfigObj(cfg_with_empty)
        self.assertEquals(cwe, {'k': '', 'k2': '', 
        'val': 'test', 'val2': [], 'val3': ['1'], 'val4': ['1', '2'], 
        'val5': ['1', '2']})

        cwe = ConfigObj(cfg_with_empty, list_values=False)
        self.assertEquals(cwe, {'k': '', 'k2': '', 
        'val': 'test', 'val2': ',', 'val3': '1,', 
        'val4': '1, 2', 'val5': '1, 2,'})
        
        testconfig3 = '''
        a = ,
        b = test,
        c = test1, test2   , test3
        d = test1, test2, test3,
        '''
        d = ConfigObj(testconfig3.split('\n'), 
                                raise_errors=True)
        self.assertEquals(d['a'], [])
        self.assertEquals(d['c'], ['test1', 'test2', 'test3'])
        self.assertEquals(d['d'], ['test1', 'test2', 'test3'])
        
        e = ConfigObj(
            testconfig3.split('\n'),
            raise_errors=True,
            list_values=False)
        self.assertEquals(e['a'], ',')    
        self.assertEquals(e['b'], 'test,')
        self.assertEquals(e['c'], 'test1, test2   , test3')
        self.assertEquals(e['d'], 'test1, test2, test3,')
        
        f = {
                 'key1': 'val1',
                 'key2': 'val2',
                 'section 1': {
                     'key1': 'val1',
                     'key2': 'val2',
                     'section 1b': {
                         'key1': 'val1',
                         'key2': 'val2',
                     },
                 },
                 'section 2': {
                     'key1': 'val1',
                     'key2': 'val2',
                     'section 2b': {
                         'key1': 'val1',
                         'key2': 'val2',
                     },
                 },
                  'key3': 'val3',
            }
        g = ConfigObj(f)
        self.assertEquals(f, g)
        
        # Testing we correctly detect badly built list values 
        # (4 of them).
        
        testconfig4 = '''
            config = 3,4,,
            test = 3,,4
            fish = ,,
            dummy = ,,hello, goodbye
        '''
        
        length = None
        try:
            ConfigObj(testconfig4.split('\n'))
        except ConfigObjError as e:
            length=len(e.errors)
        self.assertEquals(length, 4)
        
        # Testing we correctly detect badly quoted values 
        # (4 of them).
        
        testconfig5 = '''
            config = "hello   # comment
            test = 'goodbye
            fish = 'goodbye   # comment
            dummy = "hello again
        '''
        length=None
        try:
            ConfigObj(testconfig5.split('\n'))
        except ConfigObjError as e:
            length=len(e.errors)
        self.assertEquals(length, 4)
            
        # Test the _handle_comment method
        
        c = ConfigObj()
        c['foo'] = 'bar'
        c.inline_comments['foo'] = 'Nice bar'
        self.assertEquals(c.write(), ['foo = bar # Nice bar'])
        
        a = ConfigObj()
        a['DEFAULT'] = {'a' : 'fish'}
        a['a'] = '%(a)s'
        self.assertEquals(a.write(), 
                    ['a = %(a)s', '[DEFAULT]', 'a = fish'])
        
        self.assertEquals(ConfigObj({'sect': {'sect': 
                    {'foo': 'bar'}}}).write(), 
                    ['[sect]', '    [[sect]]', 
                    '        foo = bar'])
                    
        cfg = ['[sect]', '[[sect]]', 'foo = bar']
        self.assertEquals(ConfigObj(cfg).write(), cfg)
        cfg = ['[sect]', '  [[sect]]', '    foo = bar']
        self.assertEquals(ConfigObj(cfg).write(), cfg)
        cfg = ['[sect]', '    [[sect]]', '        foo = bar']

    def test_validate(self):
        config = '''
        test1=40
        test2=hello
        test3=3
        test4=5.0
        [section]
            test1=40
            test2=hello
            test3=3
            test4=5.0
            [[sub section]]
                test1=40
                test2=hello
                test3=3
                test4=5.0
        '''.split('\n')
        configspec = '''
        test1= integer(30,50)
        test2= string
        test3=integer
        test4=float(6.0)
        [section ]
            test1=integer(30,50)
            test2=string
            test3=integer
            test4=float(6.0)
            [[sub section]]
                test1=integer(30,50)
                test2=string
                test3=integer
                test4=float(6.0)
        '''.split('\n')
        
        val = Validator()
        c1 = ConfigObj(config, configspec=configspec)
        test = c1.validate(val)
        test2 = {
                'test1': True,
                'test2': True,
                'test3': True,
                'test4': False,
                'section': {
                    'test1': True,
                    'test2': True,
                    'test3': True,
                    'test4': False,
                    'sub section': {
                        'test1': True,
                        'test2': True,
                        'test3': True,
                        'test4': False,
                    },
                },
            }
        self.assertEquals(test, test2)
        
        def dummyErrorRaiser():
            val.check(c1.configspec['test4'], c1['test4'])
        self.assertRaises(VdtValueTooSmallError, dummyErrorRaiser)
        
        val_test_config = '''
            key = 0
            key2 = 1.1
            [section]
            key = some text
            key2 = 1.1, 3.0, 17, 6.8
                [[sub-section]]
                key = option1
                key2 = True'''.split('\n')
        
        val_test_configspec = '''
            key = integer
            key2 = float
            [section]
            key = string
            key2 = float_list(4)
               [[sub-section]]
               key = option(option1, option2)
               key2 = boolean'''.split('\n')
               
        val_test = ConfigObj(val_test_config, 
                            configspec=val_test_configspec)                    
        self.assertTrue(val_test.validate(val))
        
        val_test['key'] = 'text not a digit'
        val_res = val_test.validate(val)
        self.assertEquals(val_res, {'key2': True, 
                    'section': True, 'key': False})
                    
        configspec = '''
            test1=integer(30,50, default=40)
            test2=string(default="hello")
            test3=integer(default=3)
            test4=float(6.0, default=6.0)
            [section ]
                test1=integer(30,50, default=40)
                test2=string(default="hello")
                test3=integer(default=3)
                test4=float(6.0, default=6.0)
                [[sub section]]
                    test1=integer(30,50, default=40)
                    test2=string(default="hello")
                    test3=integer(default=3)
                    test4=float(6.0, default=6.0)
            '''.split('\n')
        default_test = ConfigObj(['test1=30'], configspec=configspec)
        self.assertEquals(default_test, ConfigObj({'test1': '30'}))
        self.assertEquals(default_test.defaults, [])
        self.assertEquals(default_test.default_values, {})
        self.assertTrue(default_test.validate(val))
        
        d_test = {
            'test1': 30,
            'test2': 'hello',
            'test3': 3,
            'test4': 6.0,
            'section': {
                'test1': 40,
                'test2': 'hello',
                'test3': 3,
                'test4': 6.0,
                'sub section': {
                    'test1': 40,
                    'test3': 3,
                    'test2': 'hello',
                    'test4': 6.0,
                },
            },
        }
        self.assertEquals(d_test, default_test)
        
        self.assertEquals(default_test.defaults, 
                        ['test2', 'test3', 'test4'])
                        
        self.assertEquals(default_test.default_values,  
                            {'test1': 40, 'test2': 'hello',
                                'test3': 3, 'test4': 6.0})
                                
        self.assertEquals(default_test.restore_default('test1'), 40)
        self.assertEquals(default_test['test1'], 40)
        self.assertTrue('test1' in default_test.defaults)
        
        def change(section, key): 
            section[key] = 3
        default_test.walk(change)
        self.assertEquals(default_test['section']['sub section']['test4'], 3)
        default_test.restore_defaults()
        
        d_test = {
            'test1': 40,
            'test2': "hello",
            'test3': 3,
            'test4': 6.0,
            'section': {
                'test1': 40,
                'test2': "hello",
                'test3': 3,
                'test4': 6.0,
                'sub section': {
                    'test1': 40,
                    'test2': "hello",
                    'test3': 3,
                    'test4': 6.0
        }}}
        self.assertEquals(default_test, d_test)
        
        a = ['foo = fish']
        b = ['foo = integer(default=3)']
        c = ConfigObj(a, configspec=b)
        self.assertEquals(c, ConfigObj({'foo': 'fish'}))
        
        v = Validator()
        self.assertEquals(c.validate(v), 0)
        
        self.assertEquals(c.default_values, {'foo': 3})
        
        self.assertEquals(c.restore_default('foo'), 3)
        
        repeated_1 = '''
        [dogs]
            [[__many__]] # spec for a dog
                fleas = boolean(default=True)
                tail = option(long, short, default=long)
                name = string(default=rover)
                [[[__many__]]]  # spec for a puppy
                    name = string(default="son of rover")
                    age = float(default=0.0)
        [cats]
            [[__many__]] # spec for a cat
                fleas = boolean(default=True)
                tail = option(long, short, default=short)
                name = string(default=pussy)
                [[[__many__]]] # spec for a kitten
                    name = string(default="son of pussy")
                    age = float(default=0.0)
                '''.split('\n')
                
        repeated_2 = '''
        [dogs]
        
            # blank dogs with puppies
            # should be filled in by the configspec
            [[dog1]]
                [[[puppy1]]]
                [[[puppy2]]]
                [[[puppy3]]]
            [[dog2]]
                [[[puppy1]]]
                [[[puppy2]]]
                [[[puppy3]]]
            [[dog3]]
                [[[puppy1]]]
                [[[puppy2]]]
                [[[puppy3]]]
        [cats]
        
            # blank cats with kittens
            # should be filled in by the configspec
            [[cat1]]
                [[[kitten1]]]
                [[[kitten2]]]
                [[[kitten3]]]
            [[cat2]]
                [[[kitten1]]]
                [[[kitten2]]]
                [[[kitten3]]]
            [[cat3]]
                [[[kitten1]]]
                [[[kitten2]]]
                [[[kitten3]]]
        '''.split('\n')
        
        repeated_3 = '''
        [dogs]
        
            [[dog1]]
            [[dog2]]
            [[dog3]]
        [cats]
        
            [[cat1]]
            [[cat2]]
            [[cat3]]
        '''.split('\n')
        
        repeated_4 = '''
        [__many__]
        
            name = string(default=Michael)
            age = float(default=0.0)
            sex = option(m, f, default=m)
        '''.split('\n')
        
        repeated_5 = '''
        [cats]
        [[__many__]]
            fleas = boolean(default=True)
            tail = option(long, short, default=short)
            name = string(default=pussy)
            [[[description]]]
                height = float(default=3.3)
                weight = float(default=6)
                [[[[coat]]]]
                    fur = option(black, grey, brown, "tortoise shell", default=black)
                    condition = integer(0,10, default=5)
        '''.split('\n')
        
        val = Validator()
        repeater = ConfigObj(repeated_2, configspec=repeated_1)
        self.assertTrue(repeater.validate(val))
        
        r = {
            'dogs': {
                'dog1': {
                    'fleas': True,
                    'tail': 'long',
                    'name': 'rover',
                    'puppy1': {'name': 'son of rover', 'age': 0.0},
                    'puppy2': {'name': 'son of rover', 'age': 0.0},
                    'puppy3': {'name': 'son of rover', 'age': 0.0},
                },
                'dog2': {
                    'fleas': True,
                    'tail': 'long',
                    'name': 'rover',
                    'puppy1': {'name': 'son of rover', 'age': 0.0},
                    'puppy2': {'name': 'son of rover', 'age': 0.0},
                    'puppy3': {'name': 'son of rover', 'age': 0.0},
                },
                'dog3': {
                    'fleas': True,
                    'tail': 'long',
                    'name': 'rover',
                    'puppy1': {'name': 'son of rover', 'age': 0.0},
                    'puppy2': {'name': 'son of rover', 'age': 0.0},
                    'puppy3': {'name': 'son of rover', 'age': 0.0},
                },
            },
            'cats': {
                'cat1': {
                    'fleas': True,
                    'tail': 'short',
                    'name': 'pussy',
                    'kitten1': {'name': 'son of pussy', 'age': 0.0},
                    'kitten2': {'name': 'son of pussy', 'age': 0.0},
                    'kitten3': {'name': 'son of pussy', 'age': 0.0},
                },
                'cat2': {
                    'fleas': True,
                    'tail': 'short',
                    'name': 'pussy',
                    'kitten1': {'name': 'son of pussy', 'age': 0.0},
                    'kitten2': {'name': 'son of pussy', 'age': 0.0},
                    'kitten3': {'name': 'son of pussy', 'age': 0.0},
                },
                'cat3': {
                    'fleas': True,
                    'tail': 'short',
                    'name': 'pussy',
                    'kitten1': {'name': 'son of pussy', 'age': 0.0},
                    'kitten2': {'name': 'son of pussy', 'age': 0.0},
                    'kitten3': {'name': 'son of pussy', 'age': 0.0},
                },
            },
        }
        self.assertEquals(r, repeater)
        repeater = ConfigObj(repeated_3, configspec=repeated_1)
        self.assertTrue(repeater.validate(val))

        r = {
            'cats': {
                'cat1': {'fleas': True, 'tail': 'short', 'name': 'pussy'},
                'cat2': {'fleas': True, 'tail': 'short', 'name': 'pussy'},
                'cat3': {'fleas': True, 'tail': 'short', 'name': 'pussy'},
            },
            'dogs': {
                'dog1': {'fleas': True, 'tail': 'long', 'name': 'rover'},
                'dog2': {'fleas': True, 'tail': 'long', 'name': 'rover'},
                'dog3': {'fleas': True, 'tail': 'long', 'name': 'rover'},
            },
        }
        self.assertEquals(r, repeater)
        
        repeater = ConfigObj(configspec=repeated_4)
        repeater['Michael'] = {}
        self.assertTrue(repeater.validate(val))
        
        r = {
            'Michael': {'age': 0.0, 'name': 'Michael', 'sex': 'm'},
        }
        self.assertEquals(r, repeater)
        
        repeater = ConfigObj(repeated_3, configspec=repeated_5)
        r = {
            'dogs': {'dog1': {}, 'dog2': {}, 'dog3': {}},
            'cats': {'cat1': {}, 'cat2': {}, 'cat3': {}},
        }
        self.assertEquals(r, repeater)
        self.assertTrue(repeater.validate(val))
        
        r = {
            'dogs': {'dog1': {}, 'dog2': {}, 'dog3': {}},
            'cats': {
                'cat1': {
                    'fleas': True,
                    'tail': 'short',
                    'name': 'pussy',
                    'description': {
                        'weight': 6.0,
                        'height': 3.2999999999999998,
                        'coat': {'fur': 'black', 'condition': 5},
                    },
                },
                'cat2': {
                    'fleas': True,
                    'tail': 'short',
                    'name': 'pussy',
                    'description': {
                        'weight': 6.0,
                        'height': 3.2999999999999998,
                        'coat': {'fur': 'black', 'condition': 5},
                    },
                },
                'cat3': {
                    'fleas': True,
                    'tail': 'short',
                    'name': 'pussy',
                    'description': {
                        'weight': 6.0,
                        'height': 3.2999999999999998,
                        'coat': {'fur': 'black', 'condition': 5},
                    },
                },
            },
        }
        self.assertEquals(r, repeater)
        
        # Test that interpolation is preserved for validated 
        # string values. Also check that interpolation works 
        # in configspecs.
        
        t = ConfigObj(configspec=['test = string'])
        t['DEFAULT'] = {}
        t['DEFAULT']['def_test'] = 'a'
        t['test'] = '%(def_test)s'
        self.assertEquals(t['test'], 'a')
        
        v = Validator()
        self.assertTrue(t.validate(v))
        
        t.interpolation = False
        self.assertEquals(t, ConfigObj({'test': '%(def_test)s', 
                'DEFAULT': {'def_test': 'a'}}))
                
        specs = [
            'interpolated string  = string(default="fuzzy-%(man)s")',
            '[DEFAULT]',
            'man = wuzzy',
           ]
        c = ConfigObj(configspec=specs)
        self.assertTrue(c.validate(v))
        self.assertEquals(c['interpolated string'], 'fuzzy-wuzzy')
        
        val = SimpleVal()
        config = '''
        test1=40
        test2=hello
        test3=3
        test4=5.0
        [section]
        test1=40
        test2=hello
        test3=3
        test4=5.0
            [[sub section]]
            test1=40
            test2=hello
            test3=3
            test4=5.0
        '''.split('\n')
        
        configspec = '''
        test1=''
        test2=''
        test3=''
        test4=''
        [section]
        test1=''
        test2=''
        test3=''
        test4=''
            [[sub section]]
            test1=''
            test2=''
            test3=''
            test4=''
        '''.split('\n')
        
        o = ConfigObj(config, configspec=configspec)
        self.assertTrue(o.validate(val))
        o = ConfigObj(configspec=configspec)
        self.assertFalse(o.validate(val))
        
        vtor = Validator()
        my_ini = '''
            option1 = True
            [section1]
            option1 = True
            [section2]
            another_option = Probably
            [section3]
            another_option = True
            [[section3b]]
            value = 3
            value2 = a
            value3 = 11
            '''
            
        my_cfg = '''
            option1 = boolean()
            option2 = boolean()
            option3 = boolean(default=Bad_value)
            [section1]
            option1 = boolean()
            option2 = boolean()
            option3 = boolean(default=Bad_value)
            [section2]
            another_option = boolean()
            [section3]
            another_option = boolean()
            [[section3b]]
            value = integer
            value2 = integer
            value3 = integer(0, 10)
                [[[section3b-sub]]]
                value = string
            [section4]
            another_option = boolean()
            '''
        
        cs = my_cfg.split('\n')
        ini = my_ini.split('\n')
        cfg = ConfigObj(ini, configspec=cs)
        res = cfg.validate(vtor, preserve_errors=True)
        errors = []
        for entry in flatten_errors(cfg, res):
            section_list, key, error = entry
            section_list.insert(0, '[root]')
            if key is not None:
                section_list.append(key)
            section_string = ', '.join(section_list)
            errors.append('%s%s%s' % (section_string, ' = ', error or 'missing'))
        errors.sort()
        
        E = [
        '[root], option2 = missing',
        '[root], option3 = the value "Bad_value" is of the wrong type.',
        '[root], section1, option2 = missing',
        '[root], section1, option3 = the value "Bad_value" is of the wrong type.',
        '[root], section2, another_option = the value "Probably" is of the wrong type.',
        '[root], section3, section3b, section3b-sub = missing',
        '[root], section3, section3b, value2 = the value "a" is of the wrong type.',
        '[root], section3, section3b, value3 = the value "11" is too big.',
        '[root], section4 = missing'
        ]
        
        self.assertEquals(errors, E)
    
    def test_errors(self):
        # Test the error messages and objects, in normal mode 
        # and unrepr mode.
        
        bad_syntax = '''
        key = "value"
        key2 = "value
        '''.splitlines()
        
        def dummyErrorRaiser():
            c = ConfigObj(bad_syntax)
        self.assertRaises(ParseError, dummyErrorRaiser)
    
        def dummyErrorRaiser():
            c = ConfigObj(bad_syntax, raise_errors=True)
        self.assertRaises(ParseError, dummyErrorRaiser) 
        
        def dummyErrorRaiser():
            c = ConfigObj(bad_syntax, raise_errors=True, 
                                                unrepr=True)
        self.assertRaises(UnreprError, dummyErrorRaiser)
        
        try:
            c = ConfigObj(bad_syntax)
        except Exception as e:
            self.assertTrue(isinstance(e, ConfigObjError))
            self.assertTrue(str(e), 'Parse error in value at line 3.')        
            self.assertEquals(len(e.errors), 1)
        
        try:
            c = ConfigObj(bad_syntax, unrepr=True)
        except Exception as e:
            self.assertTrue(isinstance(e, ConfigObjError))
            self.assertTrue(str(e), 'Parse error in value at line 3.')
            self.assertEquals(len(e.errors), 1)
            the_error = e.errors[0]
            self.assertTrue(isinstance(the_error, UnreprError))
        
        multiple_bad_syntax = '''
        key = "value"
        key2 = "value
        key3 = "value2
        '''.splitlines()
        
        try:
            c = ConfigObj(multiple_bad_syntax)
        except Exception as e:
            self.assertEquals(str(e), 'Parsing failed with several errors.\nFirst error at line 3.')
          
        def dummyErrorRaiser():   
            c = ConfigObj(multiple_bad_syntax, raise_errors=True)
        self.assertRaises(ParseError, dummyErrorRaiser)
        
        def dummyErrorRaiser():   
            c = ConfigObj(multiple_bad_syntax, raise_errors=True, unrepr=True)
        self.assertRaises(UnreprError, dummyErrorRaiser)
        
        try:
            c = ConfigObj(multiple_bad_syntax)
        except Exception as e:
            self.assertTrue(isinstance(e, ConfigObjError))
            self.assertEquals(str(e), "Parsing failed with several errors.\nFirst error at line 3.")
            self.assertEquals(len(e.errors), 2)

        try:
            c = ConfigObj(multiple_bad_syntax, unrepr=True)
        except Exception as e:
            self.assertTrue(isinstance(e, ConfigObjError))
            self.assertEquals(str(e), "Parsing failed with several errors.\nFirst error at line 3.")
            self.assertEquals(len(e.errors), 2)
            the_error = e.errors[1]
            self.assertTrue(isinstance(the_error, UnreprError))        
        
        unknown_name = '''
        key = "value"
        key2 = value
        '''.splitlines()
        c = ConfigObj(unknown_name)
        
        def dummyErrorRaiser():
            c = ConfigObj(unknown_name, unrepr=True)
        self.assertRaises(UnreprError, dummyErrorRaiser)    
        
        def dummyErrorRaiser():
            c = ConfigObj(unknown_name, raise_errors=True, unrepr=True)
        self.assertRaises(UnreprError, dummyErrorRaiser)    
        
    def test_unrepr_comments(self):
        config = '''
# initial comments
# with two lines
key = "value"
# section comment
[section] # inline section comment
# key comment
key = "value"
# final comment
# with two lines
'''.splitlines()
        c = ConfigObj(config, unrepr=True)
        cc = { 'key': 'value',
            'section': { 'key': 'value'}}
        self.assertEquals(c, cc)
    
        self.assertEquals(c.initial_comment, ['', '# initial comments', '# with two lines'])
        self.assertEquals(c.comments, {'section': ['# section comment'], 'key': []})
        self.assertEquals(c.inline_comments, {'section': '# inline section comment', 'key': ''})
        self.assertEquals(c['section'].comments, { 'key': ['# key comment']})
        self.assertEquals(c.final_comment, ['# final comment', '# with two lines'])

    def test_newline_terminated(self):
        c = ConfigObj()
        c.newlines = '\n'
        c['a'] = 'b'
        collector = StringIO()
        c.write(collector)
        self.assertEquals(collector.getvalue(), 'a = b\n')
        
    def test_hash_escaping(self):
        c = ConfigObj()
        c.newlines = '\n'
        c['#a'] = 'b # something'
        collector = StringIO()
        c.write(collector)
        self.assertEquals(collector.getvalue(), '"#a" = "b # something"\n')
        
        c = ConfigObj()
        c.newlines = '\n'
        c['a'] = 'b # something', 'c # something'
        collector = StringIO()
        c.write(collector)
        self.assertEquals(collector.getvalue(), 
                'a = "b # something", "c # something"\n')
                
    def test_lineendings(self):
        # NOTE: Need to use a real file because this code is 
        # only exercised when reading from the filesystem.
            
        h = open('temp', 'wb')
        crlf = '\r\n'.encode()
        h.write(crlf)
        h.close()
        c = ConfigObj('temp')
        self.assertEquals(c.newlines, '\r\n')
        h = open('temp', 'wb')
        lf = '\n'.encode()
        h.write(lf)
        h.close()
        c = ConfigObj('temp')
        self.assertEquals(c.newlines, '\n')
        os.remove('temp')
      
    def test_validate_with_copy_and_many(self):
         spec = '''
         [section]
         [[__many__]]
         value = string(default='nothing')
         '''
         config = '''
         [section]
         [[something]]
         '''
         c = ConfigObj(StringIO(config), configspec=StringIO(spec))
         v = Validator()
         r = c.validate(v, copy=True)
         self.assertEquals(c['section']['something']['value'], 'nothing')
         
    def test_configspec_with_hash(self):
        spec = ['stuff = string(default="#ff00dd")']
        c = ConfigObj(spec, _inspec=True)
        self.assertEquals(c['stuff'], 'string(default="#ff00dd")')
        c = ConfigObj(configspec=spec)
        v = Validator()
        self.assertTrue(c.validate(v))
        self.assertEquals(c['stuff'], '#ff00dd')
    
        spec = ['stuff = string(default="fish") # wooble']
        c = ConfigObj(spec, _inspec=True)
        self.assertEquals(c['stuff'], 'string(default="fish") # wooble')
    
    def test_many_check(self):
        spec = ['__many__ = integer()']
        config = ['a = 6', 'b = 7']
        c = ConfigObj(config, configspec=spec)
        v = Validator()
        self.assertTrue(c.validate(v))
        self.assertTrue(isinstance(c['a'], int))
        self.assertTrue(isinstance(c['b'], int))
        
        spec = ['[name]', '__many__ = integer()']
        config = ['[name]', 'a = 6', 'b = 7']
        c = ConfigObj(config, configspec=spec)
        v = Validator()
        self.assertTrue(c.validate(v))
        self.assertTrue(isinstance(c['name']['a'], int))
        self.assertTrue(isinstance(c['name']['b'], int))
        
        spec = ['[__many__]', '__many__ = integer()']
        config = ['[name]', 'hello = 7', '[thing]', 'fish = 0']
        c = ConfigObj(config, configspec=spec)
        v = Validator()
        self.assertTrue(c.validate(v))
        self.assertTrue(isinstance(c['name']['hello'], int))
        self.assertTrue(isinstance(c['thing']['fish'], int))

        spec = '''
        ___many___ = integer
        [__many__]
        ___many___ = boolean
        [[__many__]]
        __many__ = float
        '''.splitlines()
        
        config = '''
        fish = 8
        buggle = 4
        [hi]
        one = true
        two = false
        [[bye]]
        odd = 3
        whoops = 9.0
        [bye]
        one = true
        two = true
        [[lots]]
        odd = 3
        whoops = 9.0
        '''.splitlines()
        c = ConfigObj(config, configspec=spec)
        v = Validator()
        self.assertTrue(c.validate(v))

        self.assertTrue(isinstance(c['fish'], int))
        self.assertTrue(isinstance(c['buggle'], int))
        
        self.assertTrue(c['hi']['one'])
        self.assertFalse(c['hi']['two'])
        
        self.assertTrue(isinstance(c['hi']['bye']['odd'], float))
        self.assertTrue(isinstance(c['hi']['bye']['whoops'], float))
        
        self.assertTrue(c['bye']['one'])
        self.assertTrue(c['bye']['two'])
        
        self.assertTrue(isinstance(c['bye']['lots']['odd'], float))
        self.assertTrue(isinstance(c['bye']['lots']['whoops'], float))
        
        spec = ['___many___ = integer()']
        config = ['a = 6', 'b = 7']
        c = ConfigObj(config, configspec=spec)
        v = Validator()
        self.assertTrue(c.validate(v))
        self.assertTrue(isinstance(c['a'], int))
        self.assertTrue(isinstance(c['b'], int))
        
        spec = '''
        [__many__]
        [[__many__]]
        __many__ = float
        '''.splitlines()
        
        config = '''
        [hi]
        [[bye]]
        odd = 3
        whoops = 9.0
        [bye]
        [[lots]]
        odd = 3
        whoops = 9.0
        '''.splitlines()
        
        c = ConfigObj(config, configspec=spec)
        v = Validator()
        self.assertTrue(c.validate(v))

        self.assertTrue(isinstance(c['hi']['bye']['odd'], float))
        self.assertTrue(isinstance(c['hi']['bye']['whoops'], float))
        self.assertTrue(isinstance(c['bye']['lots']['odd'], float))
        self.assertTrue(isinstance(c['bye']['lots']['whoops'], float))
        
        
        s = ['[dog]', '[[cow]]', 'something = boolean', '[[__many__]]', 
             'fish = integer']
        c = ['[dog]', '[[cow]]', 'something = true', '[[ob]]', 
             'fish = 3', '[[bo]]', 'fish = 6']
        ini = ConfigObj(c, configspec=s)
        v = Validator()
        self.assertTrue(ini.validate(v))
        self.assertTrue(ini['dog']['cow']['something'])
        self.assertEquals(ini['dog']['ob']['fish'], 3)
        self.assertEquals(ini['dog']['bo']['fish'], 6)
        
        s = ['[cow]', 'something = boolean', '[__many__]', 
             'fish = integer']
        c = ['[cow]', 'something = true', '[ob]', 
             'fish = 3', '[bo]', 'fish = 6']
        ini = ConfigObj(c, configspec=s)
        v = Validator()
        self.assertTrue(ini.validate(v))
        self.assertTrue(ini['cow']['something'])
        self.assertEquals(ini['ob']['fish'], 3)
        self.assertEquals(ini['bo']['fish'], 6)
        
    def unexpected_validation_errors(self):
        # Although the input is nonsensical we should not crash but correctly 
        # report the failure to validate
        s = ['[cow]', 'something = boolean']
        c = ['cow = true']
        ini = ConfigObj(c, configspec=s)
        v = Validator()
        self.assertFalse(ini.validate(v))

        ini = ConfigObj(c, configspec=s)
        res = ini.validate(v, preserve_errors=True)
        check = flatten_errors(ini, res)
        
        for entry in check:
            self.assertTrue(isinstance(entry[2], ValidateError))
            self.assertEquals(str(entry[2]), "Section 'cow' was provided as a single value")
            
        s = ['something = boolean']
        c = ['[something]', 'cow = true']
        ini = ConfigObj(c, configspec=s)
        v = Validator()
        self.assertFalse(ini.validate(v))

        ini = ConfigObj(c, configspec=s)
        res = ini.validate(v, preserve_errors=True)
        check = flatten_errors(ini, res)
        
        for entry in check:
            self.assertTrue(isinstance(entry[2], ValidateError))
            self.assertEquals(str(entry[2]), "Value 'something' was provided as a section")

        s = []
        c = ['[cow]', 'dog = true']
        ini = ConfigObj(c, configspec=s)
        v = Validator()
        self.assertTrue(ini.validate(v))
        
        s = ['[cow]', 'dog = boolean']
        c = ['[cow]', 'dog = true']
        ini = ConfigObj(c, configspec=s)
        v = Validator()
        self.assertTrue(ini.validate(v, preserve_errors=True))
        
    def test_pickle(self):
        import pickle
        s = ['[cow]', 'dog = boolean']
        c = ['[cow]', 'dog = true']
        ini = ConfigObj(c, configspec=s)
        v = Validator()
        string = pickle.dumps(ini)
        new = pickle.loads(string)
        self.assertTrue(new.validate(v))
        
    def test_as_list(self):
        a = ConfigObj()
        a['a'] = 1
        self.assertEquals(a.as_list('a'), [1])
        a['a'] = (1,)
        self.assertEquals(a.as_list('a'), [1])
        a['a'] = [1]
        self.assertEquals(a.as_list('a'), [1])
        
    def test_list_interpolation(self):
        c = ConfigObj()
        c['x'] = 'foo'
        c['list'] = ['%(x)s', 3]
        self.assertEquals(c['list'], ['foo', 3])
        
    def test_extra_values(self):
        spec = ['[section]']
        infile = ['bar = 3', '[something]', 'foo = fish', '[section]', 'foo=boo']
        c = ConfigObj(infile, configspec=spec)
        self.assertEquals(c.extra_values, [])
        c.extra_values = ['bar', 'gosh', 'what']
        self.assertTrue(c.validate(Validator()))
        self.assertEquals(c.extra_values, ['bar', 'something'])
        self.assertEquals(c['section'].extra_values, ['foo'])
        self.assertEquals(c['something'].extra_values, [])
        
    def test_reset_and_clear_more(self):
        c = ConfigObj()
        c.extra_values = ['foo']
        c.defaults = ['bar']
        c.default_values = {'bar': 'baz'}
        c.clear()
        self.assertEquals(c.defaults, [])
        self.assertEquals(c.extra_values, [])
        self.assertEquals(c.default_values, {'bar': 'baz'})
        c.extra_values = ['foo']
        c.defaults = ['bar']
        c.reset()
        self.assertEquals(c.defaults, [])
        self.assertEquals(c.extra_values, [])
        self.assertEquals(c.default_values, {})
        
    def test_invalid_lists(self):
        v = ['string = val, val2, , val3']
        def dummyErrorRaiser():
            c = ConfigObj(v)
        self.assertRaises(ParseError, dummyErrorRaiser)

        v = ['string = val, val2,, val3']
        def dummyErrorRaiser():
            c = ConfigObj(v)
        self.assertRaises(ParseError, dummyErrorRaiser)

        v = ['string = val, val2,,']
        def dummyErrorRaiser():
            c = ConfigObj(v)
        self.assertRaises(ParseError, dummyErrorRaiser)

        v = ['string = val, ,']
        def dummyErrorRaiser():
            c = ConfigObj(v)
        self.assertRaises(ParseError, dummyErrorRaiser)

        v = ['string = val, ,  ']
        def dummyErrorRaiser():
            c = ConfigObj(v)
        self.assertRaises(ParseError, dummyErrorRaiser)

        v = ['string = ,,']
        def dummyErrorRaiser():
            c = ConfigObj(v)
        self.assertRaises(ParseError, dummyErrorRaiser)

        v = ['string = ,, ']
        def dummyErrorRaiser():
            c = ConfigObj(v)
        self.assertRaises(ParseError, dummyErrorRaiser)

        v = ['string = ,foo']
        def dummyErrorRaiser():
            c = ConfigObj(v)
        self.assertRaises(ParseError, dummyErrorRaiser)

        v = ['string = foo, ']
        c = ConfigObj(v)
        self.assertEquals(c['string'], ['foo'])
        
        v = ['string = foo, "']
        def dummyErrorRaiser():
            c = ConfigObj(v)
        self.assertRaises(ParseError, dummyErrorRaiser)
        
    def test_validation_with_preserve_errors(self):
        v = Validator()
        spec = ['[section]', 'foo = integer']
        c = ConfigObj(configspec=spec)
        self.assertEquals(c.validate(v, preserve_errors=True), 
                                {'section': False})
        c = ConfigObj(['[section]'], configspec=spec)
        self.assertFalse(c.validate(v))
        
        self.assertEquals(c.validate(v, preserve_errors=True), 
                    {'section': {'foo': False}})
    
            
        
if __name__ == '__main__':
    # Need to get rid of this junk below. 
    
    testconfig1 = """\
    key1= val    # comment 1
    key2= val    # comment 2
    # comment 3
    [lev1a]     # comment 4
    key1= val    # comment 5
    key2= val    # comment 6
    # comment 7
    [lev1b]    # comment 8
    key1= val    # comment 9
    key2= val    # comment 10
    # comment 11
        [[lev2ba]]    # comment 12
        key1= val    # comment 13
        # comment 14
        [[lev2bb]]    # comment 15
        key1= val    # comment 16
    # comment 17
    [lev1c]    # comment 18
    # comment 19
        [[lev2c]]    # comment 20
        # comment 21
            [[[lev3c]]]    # comment 22
            key1 = val    # comment 23"""
    
    testconfig2 = """\
    key1 = 'val1'
    key2 =   "val2"
    key3 = val3
    ["section 1"] # comment
    keys11 = val1
    keys12 = val2
    keys13 = val3
    [section 2]
    keys21 = val1
    keys22 = val2
    keys23 = val3

        [['section 2 sub 1']]
        fish = 3
    """
    
    testconfig6 = '''
    name1 = """ a single line value """ # comment
    name2 = \''' another single line value \''' # comment
    name3 = """ a single line value """
    name4 = \''' another single line value \'''
        [ "multi section" ]
        name1 = """
        Well, this is a
        multiline value
        """
        name2 = \'''
        Well, this is a
        multiline value
        \'''
        name3 = """
        Well, this is a
        multiline value
        """     # a comment
        name4 = \'''
        Well, this is a
        multiline value
        \'''  # I guess this is a comment too
    '''

    oneTabCfg = ['[sect]', '\t[[sect]]', '\t\tfoo = bar']
    twoTabsCfg = ['[sect]', '\t\t[[sect]]', '\t\t\t\tfoo = bar']
    tabsAndSpacesCfg = ['[sect]', '\t \t [[sect]]', '\t \t \t \t foo = bar']
    
    m = sys.modules.get('__main__')
    globs = m.__dict__.copy()
    a = ConfigObj(testconfig1.split('\n'), raise_errors=True)
    b = ConfigObj(testconfig2.split('\n'), raise_errors=True)
    i = ConfigObj(testconfig6.split('\n'), raise_errors=True)
    globs.update({'a': a, 'b': b, 'i': i,
        'oneTabCfg': oneTabCfg, 'twoTabsCfg': twoTabsCfg,
        'tabsAndSpacesCfg': tabsAndSpacesCfg})
    unittest.main()