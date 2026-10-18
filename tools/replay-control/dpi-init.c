// Temporary AppInit helper for this game's main GUI thread only.
typedef unsigned long DWORD;
__declspec(dllimport) DWORD __stdcall GetModuleFileNameA(void*,char*,DWORD);
__declspec(dllimport) void* __stdcall SetThreadDpiAwarenessContext(void*);
__declspec(dllimport) int __stdcall SetProcessDpiAwarenessContext(void*);
__declspec(dllimport) void* __stdcall GetStdHandle(DWORD);
__declspec(dllimport) int __stdcall WriteFile(void*,const void*,DWORD,DWORD*,void*);
int __stdcall DllMain(void* module,DWORD reason,void* reserved) {
 if(reason!=1)return 1;
 static char path[4096];DWORD n=GetModuleFileNameA(0,path,4096);
 const char name[]="HeroesOfTheStorm_x64.exe";
 int found=0;
 for(DWORD i=0;i<n;i++){int j=0;while(name[j] && i+j<n && path[i+j]==name[j])j++;if(!name[j]){found=1;break;}}
 if(!found)return 1;
 SetProcessDpiAwarenessContext((void*)-4);
 void* previous=SetThreadDpiAwarenessContext((void*)-4);
 const char ok[]="HotS DPI initializer: main thread per-monitor-v2\n";
 const char bad[]="HotS DPI initializer: context change failed\n";
 DWORD written;WriteFile(GetStdHandle((DWORD)-12),previous?ok:bad,previous?sizeof(ok)-1:sizeof(bad)-1,&written,0);
 return 1;
}
