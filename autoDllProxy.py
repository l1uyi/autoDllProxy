import os
import shutil
import subprocess
import argparse
import pefile
import platform
def openPeFile(filename):
    oPE = pefile.PE(filename)
    return oPE
def getDllName(exports , dllname):
    dll_function_name = []
    i=1
    for export in exports:
        if "Name" in export:
            funcname = str(export["Name"])[2:-1]
            tmp = '#pragma comment(linker, "/export:{}=old_{}.{},@{}")\n'.format(funcname , dllname , funcname , i)
            dll_function_name.append(tmp)
        i = i+1
    return dll_function_name
def writeC(dllFuncName,dllpath,dllname):
    evalCode = """
    MessageBox(0, (LPCSTR)"excute custom code!", (LPCSTR)"hacked by dll_proxy", 0);
    """
    template = """
//#include "pch.h"
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>
#define _CRT_SECURE_NO_DEPRECATE
#pragma warning (disable : 4996)
"""
    template2 = """
DWORD WINAPI DllProxy(LPVOID lpParameter)
{
    """ + evalCode + """
    return 0;
}

BOOL APIENTRY DllMain(HMODULE hModule,
    DWORD ul_reason_for_call,
    LPVOID lpReserved
)
{
    HANDLE threadHandle;
    switch (ul_reason_for_call)
    {
    case DLL_PROCESS_ATTACH:
        threadHandle = CreateThread(NULL, 0, DllProxy, NULL, 0, NULL);
        CloseHandle(threadHandle);
    case DLL_THREAD_ATTACH:
        break;
    case DLL_THREAD_DETACH:
        break;
    case DLL_PROCESS_DETACH:
        break;
    }
    return TRUE;
}
"""
    cpath = dllpath + "/" + "new_" + dllname.replace('.dll','.c')
    with open(cpath,"w") as file:
        file.write(template)
        for funcname in dllFuncName:
            file.write(funcname)
        file.write(template2)
        file.close()
    return cpath
def renameDll(dllpath , dllname, mode):
    if mode == 1:
        os.rename(dllname,dllpath + "/" + "old_" + dllname)
    else: 
        os.rename(dllpath + "/" + "old_" + dllname,dllname)
def setCompileEnviron(year , version ,mymachine):
    vcvarsall_path = f'C:\\Program Files\\Microsoft Visual Studio\\{year}\\{version}\\VC\\Auxiliary\\Build\\vcvarsall.bat'
    mymachine = "x86" if mymachine == "x86" else "amd64"
    proc = subprocess.Popen(f'"{vcvarsall_path}" {mymachine} & set', shell=True, stdout=subprocess.PIPE)
    for line in proc.stdout:
        try:
            decoded_line = line.decode('utf-8', errors='replace').strip()
        except UnicodeDecodeError:
            try:
                decoded_line = line.decode('gbk', errors='replace').strip()
            except UnicodeDecodeError:
                exit("环境变量解析error,可能是因为系统变量PATH中出现中文")
                continue
        if '=' in decoded_line:
            key, _, value = decoded_line.partition('=')
            os.environ[key] = value
def getCompilePath(mymachine):
    year = os.listdir("C:\\Program Files\\Microsoft Visual Studio")[0]
    edition = os.listdir(f"C:\\Program Files\\Microsoft Visual Studio\\{year}\\")[0]
    setCompileEnviron(year,edition,mymachine)
    numpath = f"C:\\Program Files\\Microsoft Visual Studio\\{year}\\{edition}\\VC\\Tools\\MSVC\\"
    numVersion = os.listdir(numpath)[0]
    host = getHost()
    compilePath = f"C:\\Program Files\\Microsoft Visual Studio\\{year}\\{edition}\\VC\\Tools\\MSVC\\{numVersion}\\bin\\Host{host}\\{mymachine}"
    return compilePath
def compileToDll(cpath , dllname):
    mymachine = "x86" if pe.FILE_HEADER.Machine == 332 else "x64"
    compilePath = getCompilePath(mymachine)
    clpath = f"{compilePath}\\cl.exe"
    folder = "tmp"
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder, exist_ok=True)
    shutil.move(cpath,folder)
    compileCmd = [clpath, '/LD', cpath ,  f'/Fe:{dllname}' , '/link' , 'user32.lib' , f"/MACHINE:{mymachine}" ]
    try:
        subprocess.run(compileCmd, cwd=os.getcwd() + "/" +folder, check=True, shell=True)
        shutil.copy(f"./{folder}/{dllname}",dllname)
    except subprocess.CalledProcessError as e:
        exit(f"编译失败，错误信息：{e}")
def getHost():
    host = platform.architecture()[0][0:2]
    host = "x64" if host == "64" else "x86"
    return host
def init():
    parser = argparse.ArgumentParser(epilog="""
    
Auto compile mode: python dll_proxy.py -D target.dll -C auto\n

Manual mode: python dll_proxy.py -D target.dll -C manually\n
    """,
    formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--dll" , "-D" , type=str , help="origin dllpath" , required=True)
    parser.add_argument("--compile", "-C", default = "manually", choices = ["manually" , "auto"] , type=str)
    args = parser.parse_args()
    dllpath, dllname = os.path.split(args.dll)
    return dllpath , dllname , args.compile
if __name__ == "__main__":
    dllpath , dllname , compile   = init()
    if dllpath == "":
        dllpath = "."
    pe = openPeFile(dllpath + "/" + dllname)
    dllFuncName = getDllName(pe.dump_dict()["Exported symbols"][1:] ,dllname)
    pe.close()
    cpath = writeC(dllFuncName , dllpath , dllname)
    print("success write template file,you can compile it")
    if compile == "auto":
        renameDll(dllpath, dllname , 1)
        try:
            compileToDll(cpath , dllname)
            print(f"success auto compile, new dll path is {dllpath}/{dllname}")
            print(f"origin dll path is {dllpath}/old_{dllname}")
        except:
            print("已自动生成对应的 .c文件,自动编译失败,请自行打开visual studio进行手动编译")
            renameDll(dllpath, dllname, 2)
    else:
        help = """
            /*
            How to use manual mode ?
            1.use visual studio to compile new.c and to new.dll
            2.rename old_dllname to old.dll, for example old_dllname is aaa.dll, you can rename aaa.dll to old_aaa.dll
            3.copy new.dll to old dll folder
            4.rename new.dll to old_dllname, for example old_dllname is aaa.dll, you can rename new.dll to aaa.dll
            5.excute the exe file, if success you can see a MessageBox
            6.now you can change new.c#DllProxy() and compile it second to excute your custom code
            */
            """
        print(help)