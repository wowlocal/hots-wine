// Create/release a D3D11 device to validate an isolated runtime's loader/ABI.
// No window, rendering loop, input, game access or network access.
typedef unsigned long DWORD;
__declspec(dllimport) void* __stdcall LoadLibraryA(const char*);
__declspec(dllimport) void* __stdcall GetProcAddress(void*,const char*);
__declspec(dllimport) int __stdcall FreeLibrary(void*);
__declspec(dllimport) void* __stdcall GetStdHandle(DWORD);
__declspec(dllimport) int __stdcall WriteFile(void*,const void*,DWORD,DWORD*,void*);
__declspec(dllimport) void __stdcall Sleep(DWORD);
__declspec(dllimport) void __stdcall ExitProcess(unsigned int);
typedef long (__stdcall *CreateDevice)(void*,unsigned int,void*,unsigned int,const unsigned int*,unsigned int,unsigned int,void**,unsigned int*,void**);
typedef unsigned long (__stdcall *Release)(void*);
void mainCRTStartup(void) {
 void* library=LoadLibraryA("d3d11.dll");
 if(!library)ExitProcess(2);
 CreateDevice create=(CreateDevice)GetProcAddress(library,"D3D11CreateDevice");
 if(!create)ExitProcess(3);
 void *device=0,*context=0;unsigned int feature=0;
 long result=create(0,1,0,0,0,0,7,&device,&feature,&context);
 char message[]="device_hresult=00000000\n";const char* hex="0123456789abcdef";
 for(int i=0;i<8;i++)message[15+i]=hex[((unsigned long)result>>(28-4*i))&15];
 DWORD written;WriteFile(GetStdHandle((DWORD)-11),message,sizeof(message)-1,&written,0);
 Sleep(8000); // Time for a read-only module-path audit from the host.
 if(context)((Release)(*(void***)context)[2])(context);
 if(device)((Release)(*(void***)device)[2])(device);
 FreeLibrary(library);ExitProcess(result<0?1:0);
}
