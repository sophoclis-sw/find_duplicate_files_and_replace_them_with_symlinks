#!/usr/local/bin/python3
import os
import hashlib
import zlib
import argparse
import pathlib
# Define a function to compute the CRC32 hash of a file
def compute_crc32(filename):
    crc = 0
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            crc = zlib.crc32(chunk, crc)
    return crc & 0xffffffff

# Define a function to compute the MD5 hash of a file
def compute_md5(filename):
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
# Define a function to find duplicate files in a directory tree using only their size. CRC32 or MD5 check will follow only for the duplicates.
def find_duplicate_files(directories, filespecs, min_size):
    print("find_duplicate_files('{}')\n".format(directories))
    duplicate_files_size = 0
    duplicate_files_count = 0
    # Create a dictionary to store files by size and CRC32 hash
    files_by_size_and_dummy_hash = {}
    # Dive in each directory
    for directory in directories:
        local_duplicates_count = 0
        local_duplicates_size = 0
        # Get individual filenames and subdirectory names for each directory
        for dirpath, dirnames, filenames in os.walk(directory):
            # Exclude Synology NAS generated subdirectories named 'eaDir'
            if ("/@eaDir/" in dirpath) or dirpath.endswith("@eaDir"):
                continue
            print("Potentially saved: {:18,d} bytes".format(local_duplicates_size, ",d"), "| {:12,d} files |".format(local_duplicates_count, ",d"), "{:18,d} bytes".format(duplicate_files_size, ",d"), "| {:12,d} files |".format(duplicate_files_count, ",d"), dirpath)
            local_duplicates_count = 0
            local_duplicates_size = 0
            # Iterrate for each file on each subdirectory
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                file_matches = False
                # Filter only the files matching the command line given filespecs, or every file otherwise
                for filespec in filespecs:
                    if pathlib.PurePath(full_path).match(filespec):
                        file_matches = True
                        break
                if file_matches == False:
                    continue
                # Ignore symbolic links
                if os.path.islink(full_path):
                    continue
                # Compute file size and CRC32 hash
                file_size = os.path.getsize(full_path)
                # duplicate_files_count += 1
                # local_duplicates_count += 1
                # Add file to dictionary
                if file_size < min_size:
                    continue
                if (file_size, 0) not in files_by_size_and_dummy_hash:
                    files_by_size_and_dummy_hash[(file_size, 0)] = [full_path]
                else:
                    files_by_size_and_dummy_hash[(file_size, 0)].append(full_path)
                    duplicate_files_count += 1
                    duplicate_files_size += file_size
                    local_duplicates_count += 1
                    local_duplicates_size += file_size
    # Filter out files that have no duplicates
    duplicate_files = {k: v for k, v in files_by_size_and_dummy_hash.items() if len(v) > 1}
    print("==================================================================================================================")
    print("Potentially {:,d} bytes".format(duplicate_files_size), "in {:,d}".format(duplicate_files_count), "duplicate files, before hash check (The hash check will only be performed on the files of the same size, to save time)")
    # print(duplicate_files)
    return duplicate_files

# Define a function to replace duplicate files with symbolic links
def replace_duplicate_files_with_links(duplicate_files, dry_run=True, use_md5=False):
    print("==================================================================================================================")
    print("replace_duplicate_files_with_links(duplicate_files, dry_run={}, use_md5={})".format(dry_run, use_md5))
    # for item in duplicate_files.items():
    #    print(item)
    if use_md5:
        print("Calculating MD5 checksums...")
    else:
        print("Calculating CRC32 checksums...")
    print("==================================================================================================================")
    duplicate_files_with_hash = {}
    for files in duplicate_files.values():
        # Link all duplicate files to the first one
        for duplicate_file in files:
            size = os.path.getsize(duplicate_file)
            if use_md5:
                hash1 = compute_md5(duplicate_file)
            else:
                hash1 = compute_crc32(duplicate_file)
            # Add file to dictionary
            if (size, hash1) not in duplicate_files_with_hash:
                duplicate_files_with_hash[(size, hash1)] = [duplicate_file]
            else:
                duplicate_files_with_hash[(size, hash1)].append(duplicate_file)
    # Filter out files that have no duplicates
    duplicate_files_new = {k: v for k, v in duplicate_files_with_hash.items() if len(v) > 1}
    # print("==============================================================================================================")
    # for item in duplicate_files_new.items():
    #    print(item)
    # print("duplicate_files_new after hash check contains {} items".format(len(duplicate_files_new.items())))
    # print("==============================================================================================================")
    duplicate_files_count = 0
    total_size = 0
    for files in duplicate_files_new.values():
        # Link all duplicate files to the first one
        first_file = files[0]
        for duplicate_file in files[1:]:
            size = os.path.getsize(duplicate_file)
            total_size += size
            duplicate_files_count += 1
            if dry_run == True:
                print("DRY RUN - symlink : " +  duplicate_file + " --> " + first_file)
                print(f"Would remove      : {duplicate_file} (size=", format(size, ",d") ," bytes)")
                print("=======================================================")
            else:
                print("Removed           : " + duplicate_file)
                print("symlink           : " + duplicate_file + " --> " + first_file)
                os.remove(duplicate_file)
                os.symlink(first_file, duplicate_file)
                print("=======================================================")
    if dry_run:
        print(f"Would remove", format(duplicate_files_count, ",d"), "files, total size =", format(total_size, ",d"), "bytes")
    else:
        print(f"Removed", format(duplicate_files_count, ",d"), " files, total size =", format(total_size, ",d"), " bytes")
    print(format(duplicate_files_count, ",d"), " duplicate files total size after hash check: ", format(total_size, ",d"), "bytes")

if __name__ == "__main__":
    # Parse command line arguments and run
    parser = argparse.ArgumentParser(description="Find and replace duplicate files with symbolic links in a given directory tree, or in multiple directories.")
    parser.add_argument("-f",   "--file",     metavar="<FILE SPEC>", action="append",                        required=False, help="The file spec to search for duplicates. For example -f "'*.JPG'" You can add multiple file specs using the -f for each one of them.")
    parser.add_argument("-d",   "--dir",      metavar="<DIRECTORY>", action="append",     type=pathlib.Path, required=True,  help="The directory to search for duplicates. You can add multiple directories using the -d for each one of them.")
    parser.add_argument("-r",   "--remove",                          action="store_true",                                    help="Remove the duplicate files from directory, and replace them with symbolic links.")
    parser.add_argument("-md5",                                      action="store_true",                                    help="Calculate the MD5 hash for the duplicate files to increase reliability. By default CRC32 will be used for speed.")
    parser.add_argument("-m",   "--min_size",                                             type=int,                          help="Minimum file size to consider (skip smaller files)")
    dry_run = True
    args = parser.parse_args()
    if args.dir == []:
        print("directory:   '{}'".format(args.dir))
        print("At least one directory should be given in the command line. Exiting...")
        exit()
    else:
        print(args.dir)
    if args.file != []:
        print(args.file)
    if not args.min_size is None:
        min_file_size = args.min_size
    else:
        min_file_size = 1
    remove_and_link = args.remove
    use_md5 = args.md5
    directories = []
    for directory in args.dir:
        directories.append(os.path.abspath(directory))
    # if no file patterns are given to look for, any file would match the search in the given directories
    filespecs = []
    if args.file is None:
        filespecs = ['*']
    else:
        for filespec in args.file:
            filespecs.append(filespec)
    # If the --remove-and-link argument is not present, the dry_run is True by default
    if remove_and_link == True:
        dry_run = False
    print("Dry run:        {}".format(dry_run))
    print("Remove Files:   {}".format(remove_and_link))
    if args.md5:
        print("Use MD5:        {}".format(use_md5), "(Using MD5 instead of CRC32 for the duplicate files -> slower)")
    else:
        print("Use MD5:        {}".format(use_md5), "(Using CRC32 instead of MD5 for the duplicate files -> faster)")
    for i in range(len(directories)):
        print("Directory {}:    {}".format(i+1, directories[i]))
    for i in range(len(filespecs)):
        print("Filespec  {}:    {}".format(i+1, filespecs[i]))

    duplicate_files = find_duplicate_files(directories, filespecs, min_file_size)
    replace_duplicate_files_with_links(duplicate_files, dry_run, use_md5)
