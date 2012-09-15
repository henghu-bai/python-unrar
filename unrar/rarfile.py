# -*- coding: utf-8 -*-
# Author: Matías Bordese

import ctypes
import sys

from unrar import constants
from unrar import unrarlib


__all__ = ["BadRarFile", "is_rarfile", "RarFile", "RarInfo"]


class BadRarFile(Exception):
    """RAR file error."""


def is_rarfile(filename):
    """Return true if file is a valid RAR file."""
    mode = constants.RAR_OM_LIST_INCSPLIT
    archive = unrarlib.RAROpenArchiveDataEx(filename, mode=mode)
    try:
        handle = unrarlib.RAROpenArchiveEx(ctypes.byref(archive))
    except unrarlib.UnrarException:
        return False
    unrarlib.RARCloseArchive(handle)
    return (archive.OpenResult == constants.SUCCESS)


class RarInfo(object):
    """Class with attributes describing each member in the RAR archive."""

    __slots__ = (
            'filename',
            'date_time',
            'compress_type',
            'comment',
            'create_system',
            'extract_version',
            'flag_bits',
            'CRC',
            'compress_size',
            'file_size',
            '_raw_time',
        )

    def __init__(self, header):
        """Initialize a RarInfo object with a member header data."""
        self.filename = header.FileNameW
        self._raw_time = header.FileTime
        self.date_time = unrarlib.dostime_to_timetuple(header.FileTime)
        self.compress_size = header.PackSize + (header.PackSizeHigh << 32)
        self.file_size = header.UnpSize + (header.UnpSizeHigh << 32)
        self.create_system = header.HostOS
        self.extract_version = header.UnpVer
        self.CRC = header.FileCRC
        self.flag_bits = header.Flags
        if header.CmtState == constants.RAR_COMMENTS_SUCCESS:
            self.comment = header.CmtBuf.value
        else:
            self.comment = None


class RarFile(object):
    """RAR archive file."""

    def __init__(self, filename, mode='r', pwd=None):
        """Load RAR archive file with mode read only "r"."""
        self.filename = filename
        mode = constants.RAR_OM_LIST_INCSPLIT

        archive = unrarlib.RAROpenArchiveDataEx(filename, mode=mode)
        handle = self._open(archive)

        # assert(archive.OpenResult == constants.SUCCESS)
        self.pwd = pwd
        self.filelist = []
        self.NameToInfo = {}
        if archive.CmtState == constants.RAR_COMMENTS_SUCCESS:
            self.comment = archive.CmtBuf.value
        else:
            self.comment = None
        self._load_metadata(handle)
        self._close(handle)

    def _read_header(self, handle):
        """Read current member header into a RarInfo object."""
        rarinfo = None
        header_data = unrarlib.RARHeaderDataEx()
        res = unrarlib.RARReadHeaderEx(handle, ctypes.byref(header_data))
        if res != constants.ERAR_END_ARCHIVE:
            rarinfo = RarInfo(header=header_data)
        return rarinfo

    def _process_current(self, handle, op, dest_path=None, dest_name=None):
        """Process current member with 'op' operation."""
        unrarlib.RARProcessFile(handle, op, dest_path, dest_name)

    def _load_metadata(self, handle):
        """Load archive members metadata."""
        rarinfo = self._read_header(handle)
        while rarinfo:
            self.filelist.append(rarinfo)
            self.NameToInfo[rarinfo.filename] = rarinfo
            self._process_current(handle, constants.RAR_SKIP)
            rarinfo = self._read_header(handle)

    def _open(self, archive):
        """Open RAR archive file."""
        try:
            handle = unrarlib.RAROpenArchiveEx(ctypes.byref(archive))
        except unrarlib.UnrarException:
            raise BadRarFile("Invalid RAR file.")
        return handle

    def _close(self, handle):
        """Close RAR archive file."""
        try:
            unrarlib.RARCloseArchive(handle)
        except unrarlib.UnrarException:
            raise BadRarFile("RAR archive close error.")

    def namelist(self):
        """Return a list of file names in the archive."""
        names = []
        for member in self.filelist:
            names.append(member.filename)
        return names

    def setpassword(self, pwd):
        """Set default password for encrypted files."""
        self._pwd = pwd

    def getinfo(self, name):
        """Return the instance of RarInfo given 'name'."""
        rarinfo = self.NameToInfo.get(name)
        if rarinfo is None:
            raise KeyError('There is no item named %r in the archive' % name)
        return rarinfo

    def infolist(self):
        """Return a list of class RarInfo instances for files in the
        archive."""
        return self.filelist

    def printdir(self):
        """Print a table of contents for the RAR file."""
        print "%-46s %19s %12s" % ("File Name", "Modified    ", "Size")
        for rarinfo in self.filelist:
            date = "%d-%02d-%02d %02d:%02d:%02d" % rarinfo.date_time[:6]
            print "%-46s %s %12d" % (rarinfo.filename, date, rarinfo.file_size)

    def testrar(self):
        """Read all the files and check the CRC."""
        error = None
        rarinfo = None
        archive = unrarlib.RAROpenArchiveDataEx(
            self.filename, mode=constants.RAR_OM_EXTRACT)
        handle = self._open(archive)

        try:
            rarinfo = self._read_header(handle)
            while rarinfo is not None:
                self._process_current(handle, constants.RAR_TEST)
                rarinfo = self._read_header(handle)
        except unrarlib.UnrarException:
            error = rarinfo.filename if rarinfo else self.filename
        finally:
            self._close(handle)
        return error

    def extract(self, member, path=None, pwd=None):
        """Extract a member from the archive to the current working directory,
           using its full name. Its file information is extracted as accurately
           as possible. `member' may be a filename or a RarInfo object. You can
           specify a different directory using `path'.
        """
        if isinstance(member, RarInfo):
            member = member.filename
        self._extract_members([member], path, pwd)

    def extractall(self, path=None, members=None, pwd=None):
        """Extract all members from the archive to the current working
           directory. `path' specifies a different directory to extract to.
           `members' is optional and must be a subset of the list returned
           by namelist().
        """
        if members is None:
            members = self.namelist()
        self._extract_members(members, path, pwd)

    def _extract_members(self, members, targetpath, pwd):
        """Extract the RarInfo objects 'members' to a physical
           file on the path targetpath.
        """
        archive = unrarlib.RAROpenArchiveDataEx(
            self.filename, mode=constants.RAR_OM_EXTRACT)
        handle = self._open(archive)

        password = pwd or self.pwd
        if password is not None:
            unrarlib.RARSetPassword(handle, password)

        try:
            rarinfo = self._read_header(handle)
            while rarinfo is not None:
                if rarinfo.filename in members:
                    self._process_current(
                        handle, constants.RAR_EXTRACT, targetpath)
                else:
                    self._process_current(handle, constants.RAR_SKIP)
                rarinfo = self._read_header(handle)
        except unrarlib.UnrarException:
            raise BadRarFile("Bad RAR archive data.")
        finally:
            self._close(handle)


def main(args=None):
    import textwrap
    USAGE = textwrap.dedent("""\
        Usage:
            rarfile.py -l rarfile.rar        # Show listing of a rarfile
            rarfile.py -t rarfile.rar        # Test if a rarfile is valid
            rarfile.py -e rarfile.rar target # Extract rarfile into target dir
        """)

    valid_args = {'-l': 2, '-e': 3, '-t':2}
    if args is None:
        args = sys.argv[1:]

    cmd = args and args[0] or None
    if not cmd or cmd not in valid_args or len(args) != valid_args[cmd]:
        print USAGE
        sys.exit(1)

    if cmd == '-l':
        # list
        rf = RarFile(args[1], 'r')
        rf.printdir()
    elif cmd == '-t':
        # test
        rf = RarFile(args[1], 'r')
        err = rf.testrar()
        if err:
            print("The following enclosed file is corrupted: {!r}".format(err))
        print "Done testing"
    elif cmd == '-e':
        # extract
        rf = RarFile(args[1], 'r')
        dest = args[2]
        rf.extractall(path=dest)


if __name__ == "__main__":
    main()