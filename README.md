# 特点
1.自动调用编译器编译dll

选择一个dll文件, autoDllProxy 会自动生成对应的能够对该dll文件进行代理的新dll。兼容x86和x86_64。

2.自动探测调用指定dll的exe

支持dll替换后自动探测当前文件夹下哪些exe在运行时会调用该dll，结果保存在当前目录下的result.txt中

# 安装

python

```
pip install -r requirements.txt
```

编译器

autoDllProxy会调用visual studio自带的cl.exe编译器进行编译,请自行安装visual studio。 社区版和专业版均可

# 使用方法

```
usage: dll_proxy.py [-h] --dll DLL [--compile {manually,auto}] [--detect {manually,auto}]
                                                                                         
optional arguments:                                                                      
  -h, --help            show this help message and exit
  --dll DLL, -D DLL     origin dllpath
  --compile {manually,auto}, -C {manually,auto}
                        auto compile .c to .dll
  --detect {manually,auto}
                        auto detect vulnerable exe

Auto compile mode: python dll_proxy.py -D target.dll -C auto --detect auto

Manual mode: python dll_proxy.py -D target.dll -C manually --detect manually

```

自动生成dll，自动探测

```
python dll_proxy.py -D target.dll -C auto --detect auto
```

自动生成dll，不探测

```
python dll_proxy.py -D target.dll -C auto --detect manually
```

只生成.c文件，不生成dll，不探测

```
python dll_proxy.py -D target.dll -C manually
```

不生成.c文件，不生成dll，自动探测（适用于手动编译dll后执行）

```
python dll_proxy.py -D target.dll -C None --detect auto
```

注意：手动编译后需将 原.dll 重命名为 old_原.dll ,新dll重命名为 原.dll
