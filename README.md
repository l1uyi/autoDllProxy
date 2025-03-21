# autoDllProxy
选择一个dll文件，autoDllProxy会生成对应的dll文件进行代理。

兼容64位和32位的dll文件。

# 安装依赖

python

```
pip install -r requirements.txt
```

编译器

autoDllProxy会调用visual studio自带的cl.exe编译器进行编译,请自行安装visual studio。 社区版和专业版均可

# 使用方法

自动编译

```
python dll_proxy.py -D target.dll -C auto
```

手动编译：只会生成 .c文件，需要手动使用visual studio进行编译

```
python dll_proxy.py -D target.dll -C manually
```

运行脚本后，target.dll 会重命名为old_target.dll , 新生成的dll文件名为target.dll。

此时运行对应的exe，若出现弹窗则说明代理成功。

若出现报错且报错信息为 7b，则说明exe加载dll时进行了合法性校验。
