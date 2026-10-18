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
__declspec(dllimport) int __stdcall SetWindowPos(void*,void*,int,int,int,int,unsigned int);
__declspec(dllimport) int __stdcall EnumDisplaySettingsW(const unsigned short*,DWORD,void*);
__declspec(dllimport) long __stdcall ChangeDisplaySettingsW(void*,DWORD);
__declspec(dllimport) long long __stdcall SendMessageA(void*,unsigned int,ULONG_PTR,long long);
__declspec(dllimport) int __stdcall GetSystemMetrics(int);
__declspec(dllimport) void* __stdcall GetStdHandle(DWORD);
__declspec(dllimport) int __stdcall WriteFile(void*,const void*,DWORD,DWORD*,void*);
__declspec(dllimport) int __stdcall SetProcessDPIAware(void);
__declspec(dllimport) int __stdcall ClipCursor(const RECT*);
__declspec(dllimport) void __stdcall Sleep(DWORD);
__declspec(dllimport) char* __stdcall GetCommandLineA(void);
__declspec(dllimport) void __stdcall ExitProcess(unsigned int);
void mainCRTStartup(void) {
 SetProcessDPIAware();
 void* window=FindWindowA(0,"Heroes of the Storm");
 if(!window) ExitProcess(2);
 SetForegroundWindow(window);
 Sleep(250);
 char* line=GetCommandLineA();
 char* keys=0;
 for(char* p=line;*p;p++) if(p[0]==' ' && p[1]=='u' && p[2]=='n' && p[3]=='c' && p[4]=='l' && p[5]=='i' && p[6]=='p') ExitProcess(ClipCursor(0)?0:8);
 for(char* p=line;*p;p++) if(p[0]==' ' && p[1]=='q' && p[2]=='u' && p[3]=='e' && p[4]=='r' && p[5]=='y') {
  RECT r;GetClientRect(window,&r);int values[4]={r.right-r.left,r.bottom-r.top,GetSystemMetrics(0),GetSystemMetrics(1)};
  char output[128];int length=0;
  for(int i=0;i<4;i++) {char n[16];int c=0,v=values[i];do{n[c++]='0'+v%10;v/=10;}while(v);while(c)output[length++]=n[--c];output[length++]=i==3?'\n':' ';}
  DWORD written;WriteFile(GetStdHandle((DWORD)-11),output,length,&written,0);ExitProcess(0);
 }
 for(char* p=line;*p;p++) if(p[0]==' ' && p[1]=='j' && p[2]=='u' && p[3]=='m' && p[4]=='p' && p[5]=='=') {
  int n=0;for(char* q=p+6;*q>='0' && *q<='9';q++)n=n*10+(*q-'0');if(n>950)ExitProcess(4);
  int x=3456*(785000+195*n)/1000000,y=2234*162/1000;
  long long point=(unsigned int)((y<<16)|(x&0xffff));
  SendMessageA(window,0x200,0,point);Sleep(150);
  SendMessageA(window,0x201,1,point);Sleep(100);
  SendMessageA(window,0x202,0,point);ExitProcess(0);
 }
 for(char* p=line;*p;p++) if(p[0]==' ' && p[1]=='d' && p[2]=='i' && p[3]=='s' && p[4]=='p' && p[5]=='l' && p[6]=='a' && p[7]=='y' && p[8]=='=' && p[9]=='1') {
  volatile unsigned char mode[220];for(int i=0;i<220;i++) mode[i]=0;
  *(unsigned short*)(mode+68)=220;
  if(!EnumDisplaySettingsW(0,(DWORD)-1,(void*)mode)) ExitProcess(6);
  *(DWORD*)(mode+72)=0x180000; // DM_PELSWIDTH | DM_PELSHEIGHT
  *(DWORD*)(mode+172)=3456;*(DWORD*)(mode+176)=2234;
  ExitProcess(ChangeDisplaySettingsW((void*)mode,4)==0 ? 0 : 7);
 }
 // Explicit native-resolution borderless client; needed with an older live Wine desktop.
 for(char* p=line;*p;p++) if(p[0]==' ' && p[1]=='n' && p[2]=='a' && p[3]=='t' && p[4]=='i' && p[5]=='v' && p[6]=='e' && p[7]=='=' && p[8]=='1') {
  ExitProcess(SetWindowPos(window,0,0,0,3456,2234,0x24) ? 0 : 5);
 }
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
  int control=0,shift=0;
  if(key=='^') {control=1;key=*++p;if(!key) break;}
  if(key=='~') key=13;
  if(key==':') {key=0xba;shift=1;}
  if(key>='a' && key<='z') key-=32;
  if(!((key>='A' && key<='Z') || (key>='0' && key<='9') || key==13 || key==0xba)) continue;
  if(control) keybd_event(0x11,0,0,0);
  if(shift) keybd_event(0x10,0,0,0);
  keybd_event(key,0,0,0);Sleep(60);keybd_event(key,0,2,0);Sleep(200);
  if(shift) keybd_event(0x10,0,2,0);
  if(control) keybd_event(0x11,0,2,0);
 }
 ExitProcess(0);
}
