from distutils import msvc9compiler
import subprocess
import os

def compile(filename, outputfilename, arch='x86', vcver=None):
    if vcver == None:
        if os.getenv('MSVCVER'):
            vcver = float(os.getenv('MSVCVER'))
        else:
            vcver = msvc9compiler.get_build_version()
    vcvars = msvc9compiler.find_vcvarsall(vcver)
    if not vcvars:  # My VS 2008 Standard Edition doesn't have vcvarsall.bat
        vsbase = msvc9compiler.VS_BASE % vcver
        productdir = msvc9compiler.Reg.get_value(r"%s\Setup\VC" % vsbase,
                                                 "productdir")
        bat = 'vcvars%d.bat' % (arch == 'x86' and 32 or 64)
        vcvars = os.path.join(productdir, 'bin',  bat)

    path = os.path.splitext(outputfilename)
    objfilename = path[0] + '.obj'
    p = subprocess.Popen('"%s" %s & cl %s /Fe%s /Fo%s' % (vcvars, arch, filename, outputfilename, objfilename),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    try:
        stdout, stderr = p.communicate()
        if p.wait() != 0:
            raise Exception(stderr.decode("mbcs"))
        os.remove(objfilename)
    finally:
        p.stdout.close()
        p.stderr.close()

#try:
#    compile('inject_python.cpp', 'inject_python_32.exe', 'x86', 10.0)
#except:
#    pass
#try:
#    compile('inject_python.cpp', 'inject_python_64.exe', 'amd64', 10.0)
#except:
#    pass