// Local, one-shot replay keyboard helper. No hooks, networking or persistence.
typedef unsigned long DWORD;
typedef unsigned long long ULONG_PTR;
typedef struct { long left,top,right,bottom; } RECT;
typedef struct { long x,y; } POINT;
__declspec(dllimport) void* __stdcall FindWindowA(const char*, const char*);
__declspec(dllimport) int __stdcall SetForegroundWindow(void*);
__declspec(dllimport) void __stdcall keybd_event(unsigned char,unsigned char,DWORD,ULONG_PTR);
__declspec(dllimport) int __stdcall GetClientRect(void*,RECT*);
__declspec(dllimport) int __stdcall ClientToScreen(void*,POINT*);
__declspec(dllimport) int __stdcall SetCursorPos(int,int);
__declspec(dllimport) void __stdcall mouse_event(DWORD,DWORD,DWORD,DWORD,ULONG_PTR);
__declspec(dllimport) void __stdcall Sleep(DWORD);
__declspec(dllimport) char* __stdcall GetCommandLineA(void);
__declspec(dllimport) void __stdcall ExitProcess(unsigned int);
void mainCRTStartup(void) {
 void* window=FindWindowA(0,"Heroes of the Storm");
 if(!window) ExitProcess(2);
 SetForegroundWindow(window);
 Sleep(250);
 char* line=GetCommandLineA();
 char* keys=0;
 // Seek on the visible standard replay timeline; value is thousandths of duration.
 // Coordinates are derived from the inspected 1728x1117 client screenshot.
 for(char* p=line;*p;p++) if(p[0]==' ' && p[1]=='s' && p[2]=='e' && p[3]=='e' && p[4]=='k' && p[5]=='=') {
  int n=0;for(char* q=p+6;*q>='0' && *q<='9';q++) n=n*10+(*q-'0');
  if(n>950) ExitProcess(4);
  RECT r;GetClientRect(window,&r);
  POINT pt={(r.right-r.left)*(785000+195*n)/1000000,(r.bottom-r.top)*162/1000};
  ClientToScreen(window,&pt);SetCursorPos(pt.x,pt.y);Sleep(100);
  mouse_event(2,0,0,0,0);Sleep(60);mouse_event(4,0,0,0,0);ExitProcess(0);
 }
 for(char* p=line;*p;p++) if(p[0]==' ' && p[1]=='k' && p[2]=='e' && p[3]=='y' && p[4]=='s' && p[5]=='=') {keys=p+6;break;}
 if(!keys) ExitProcess(3);
 for(char* p=keys;*p && *p!=' ';p++) {
  unsigned char key=*p;
  if(key>='a' && key<='z') key-=32;
  if(!((key>='A' && key<='Z') || (key>='0' && key<='9'))) continue;
  keybd_event(key,0,0,0);Sleep(60);keybd_event(key,0,2,0);Sleep(200);
 }
 ExitProcess(0);
}
