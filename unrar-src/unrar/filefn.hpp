#ifndef _RAR_FILEFN_
#define _RAR_FILEFN_

enum MKDIR_CODE {MKDIR_SUCCESS,MKDIR_ERROR,MKDIR_BADPATH};

MKDIR_CODE MakeDir(const wchar *Name,bool SetAttr,uint Attr);
bool CreatePath(const wchar *Path,bool SkipLastName);
void SetDirTime(const wchar *Name,RarTime *ftm,RarTime *ftc,RarTime *fta);
bool IsRemovable(const wchar *Name);

#ifndef SFX_MODULE
int64 GetFreeDisk(const wchar *Name);
#endif


bool FileExist(const wchar *Name);
bool WildFileExist(const wchar *Name);
bool IsDir(uint Attr);
bool IsUnreadable(uint Attr);
bool IsLink(uint Attr);
void SetSFXMode(const wchar *FileName);
void EraseDiskContents(const wchar *FileName);
bool IsDeleteAllowed(uint FileAttr);
void PrepareToDelete(const wchar *Name);
uint GetFileAttr(const wchar *Name);
bool SetFileAttr(const wchar *Name,uint Attr);

enum CALCFSUM_FLAGS {CALCFSUM_SHOWTEXT=1,CALCFSUM_SHOWALL=2,CALCFSUM_CURPOS=4};

void CalcFileSum(File *SrcFile,uint *CRC32,byte *Blake2,uint Threads,int64 Size=INT64NDF,uint Flags=0);

bool RenameFile(const wchar *SrcName,const wchar *DestName);
bool DelFile(const wchar *Name);
bool DelDir(const wchar *Name);

#if defined(_WIN_ALL) && !defined(_WIN_CE)
bool SetFileCompression(const wchar *Name,bool State);
#endif





#endif
