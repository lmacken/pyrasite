#include <stdio.h>
#include <Windows.h>

//TODO
// support both ansi and unicode in the code (path for injection might have non english letters), how does python handle unicode in PyRun_SimpleString ?
// i checked on windows 7 64bit running 32bit python 2.7, check on other windows versions, and other python versions
// try maybe to write a code to auto figure out in which modules the Python functions are, maybe with EnumProcessModules
// do i need to statically compile the runtime libraries here ? (compile with VS2008 which is python 2.7 runtime maybe?)
// check the 64bit process injection especially in the context of ASLR
// in python 64 bit building, does disttools choose the 64 bit compiler?
// if python extension restore previous privilieges after running ?
// set only the privilieges needed for what i want to do..
// itanium support?

// Can be compiled in visual studio command prompt with: cl.exe inject_python.cpp

#pragma comment(lib, "kernel32.lib")
#pragma comment(lib, "user32.lib")
#pragma comment(lib, "advapi32.lib")

int RaisePrivileges()
{
	int retCode = 0;
	HANDLE hToken;
	TOKEN_PRIVILEGES tp;
	TOKEN_PRIVILEGES oldtp;
	DWORD dwSize = sizeof(TOKEN_PRIVILEGES);          
	LUID luid;          

	if (!OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, &hToken))
	{
		retCode = 1;
		goto error1;
	}
	if (!LookupPrivilegeValue(NULL, SE_DEBUG_NAME, &luid))
	{
		retCode = 2;
		goto error2;
	}
	ZeroMemory(&tp, sizeof(tp));
	tp.PrivilegeCount = 1;
	tp.Privileges[0].Luid = luid;
	tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;
	if (!AdjustTokenPrivileges(hToken, FALSE, &tp, sizeof(TOKEN_PRIVILEGES), &oldtp, &dwSize))
	{
		retCode = 3;
		goto error2;
	}
	error2:
	CloseHandle(hToken);
	error1:
	return retCode;
}

typedef struct
{
	HMODULE (__stdcall *pGetModuleHandle)(LPCSTR);
	FARPROC (__stdcall *pGetProcAddress)(HMODULE, LPCSTR);
	char ModuleName[9];
	char PyGILState_Ensure[18];
	char PyRun_SimpleString[19];
	char PyGILState_Release[19];
	char *Code;
} REMOTEDATA;

static DWORD WINAPI ExecutePythonCode(REMOTEDATA *data)
{
	DWORD retCode = 0;
	HMODULE hModule = data->pGetModuleHandle(data->ModuleName);
	if (hModule != NULL)
	{
		int (__cdecl *a)() = reinterpret_cast<int (__cdecl *)()>(data->pGetProcAddress(hModule, data->PyGILState_Ensure));
		if (a != NULL)
		{
			int ret = a();

			void (__cdecl *b)(char *) = reinterpret_cast<void (__cdecl *)(char *)>(data->pGetProcAddress(hModule, data->PyRun_SimpleString));
			if (b != NULL)
			{
				b(data->Code);
			} else {
				retCode = 3;
			}
			
			void (__cdecl *c)(int) = reinterpret_cast<void (__cdecl *)(int)>(data->pGetProcAddress(hModule, data->PyGILState_Release));
			if (c != NULL)
			{
				c(ret);
			} else {
				retCode = 4;
			}
		} else {
			retCode = 2;
		}
	} else {
		retCode = 1;
	}
	return retCode;
}

static void AfterExecutePythonCode()
{
}

int InjectPythonCode(HANDLE hProcess, const char *code, char *moduleName)
{
	int retCode = 0;
	REMOTEDATA data;
	int cbCodeSize = (PBYTE)AfterExecutePythonCode - (PBYTE)ExecutePythonCode;
	void* remoteCodeString = VirtualAllocEx(hProcess, NULL, strlen(code) + 1, MEM_COMMIT, PAGE_READWRITE);
	if (remoteCodeString == NULL)
	{
		retCode = 1;
		goto error1;
	}
	void* remoteCode = VirtualAllocEx(hProcess, NULL, cbCodeSize, MEM_COMMIT, PAGE_EXECUTE);
	if (remoteCode == NULL)
	{
		retCode = 2;
		goto error2;
	}
	void* remoteData = VirtualAllocEx(hProcess, NULL, sizeof(data), MEM_COMMIT, PAGE_READWRITE);
	if (remoteData == NULL)
	{
		retCode = 3;
		goto error3;
	}
	if (!WriteProcessMemory(hProcess, remoteCodeString, (void*)code, strlen(code) + 1, NULL))
	{
		retCode = 4;
		goto error3;
	}
	data.pGetModuleHandle = GetModuleHandle;
	data.pGetProcAddress = GetProcAddress;
	strcpy_s(data.ModuleName, moduleName);
	strcpy_s(data.PyGILState_Ensure, "PyGILState_Ensure");
	strcpy_s(data.PyRun_SimpleString, "PyRun_SimpleString");
	strcpy_s(data.PyGILState_Release, "PyGILState_Release");
	data.Code = (char *)remoteCodeString;
	if (!WriteProcessMemory(hProcess, remoteData, (void*)&data, sizeof(data), NULL))
	{
		retCode = 5;
		goto error3;
	}
	if (!WriteProcessMemory(hProcess, remoteCode, (void*)ExecutePythonCode, cbCodeSize, NULL))
	{
		retCode = 6;
		goto error3;
	}
	HANDLE hRemoteThread = CreateRemoteThread(hProcess, NULL, 0, (LPTHREAD_START_ROUTINE)remoteCode, remoteData, 0, NULL);
	if (!hRemoteThread)
	{
		retCode = 7;
		goto error3;
	}
	if (WaitForSingleObject(hRemoteThread, INFINITE) == WAIT_FAILED)
	{
		retCode = 8;
		goto error4;
	}
	DWORD exitCode;
	if (!GetExitCodeThread(hRemoteThread, &exitCode))
	{
		retCode = 9;
		goto error4;
	}
	if (exitCode != 0)
	{
		retCode = 10;
		goto error4;
	}	
	error4:
	CloseHandle(hRemoteThread);
	error3:
	VirtualFreeEx(hProcess, remoteData, sizeof(data), MEM_RELEASE);
	error2:
	VirtualFreeEx(hProcess, remoteCode, cbCodeSize, MEM_RELEASE);
	error1:
	VirtualFreeEx(hProcess, remoteCodeString, strlen(code) + 1, MEM_RELEASE);
	return retCode;
}

int InjectPythonCodeToPID(DWORD pid, const char *code)
{
	char versions[][9] = { "Python36", "Python35", "Python34", "Python33", "Python32", "Python31", "Python30", "Python27", "Python26", "Python25", "Python24" };
	unsigned int numVersions = 11;
	unsigned int i;
	int retCode = 0;
	int ret;
	BOOL is32Bit;
	HANDLE hProcess = OpenProcess(PROCESS_ALL_ACCESS, false, pid);
	if (!hProcess)
	{
		retCode = 1;
		goto error1;
	}
	//TODO this requires windows xp an above, later check if the function exists first...
	if (!IsWow64Process(hProcess, &is32Bit))
	{
		retCode = 2;
		goto error2;
	}
#ifdef _WIN64
	if (is32Bit)
	{
		retCode = 5;
		goto error2;
	}
#else
	BOOL amI32Bit;
	IsWow64Process(GetCurrentProcess(), &amI32Bit);
	if (amI32Bit && !is32Bit)
	{
		retCode = 5;
		goto error2;
	}
#endif
	for (i = 0; i < numVersions; ++i)
	{
		ret = InjectPythonCode(hProcess, code, versions[i]);
		if (ret == 0)
		{
			break;
		}
		if (ret != 10)
		{
			retCode = 3;
			goto error2;
		}
	}
	if (ret != 0)
	{
		retCode = 4;
		goto error2;
	}
	error2:
	CloseHandle(hProcess);
	error1:
	return retCode;
}

int main(int argc, char *argv[])
{
	if (argc != 3)
	{
		fprintf(stderr, "Usage: %s <pid> <code>\n", argv[0]);
		return 1;
	}
	DWORD pid = atoi(argv[1]);
	char* code = argv[2];
	int ret;
	ret = RaisePrivileges();
	if (ret)
	{
		fprintf(stderr, "Could not raise privileges, return value %d, error code %d\n", ret, GetLastError());
		return 10 + ret;
	}
	ret = InjectPythonCodeToPID(pid, code);
	if (ret)
	{
		fprintf(stderr, "Could not inject code, return value %d, error code %d\n", ret, GetLastError());
		return 20 + ret;
	}
	return 0;
}
