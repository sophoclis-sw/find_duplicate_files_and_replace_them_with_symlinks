# ./
As the title of the repository suggests, this Python script searches for duplicate files in a directory tree, or in a list of directory trees, and it replaces them with a symbolic link, keeping only one copy.

It's meant to run on Linux or MacOS, since both operating systems support symbolic links.
If you'd like to run it on Windows, you'd need to modify the code to create Microsoft's version of symbolic links instead. 
I haven't tried that yet.

By default it's running in "Dry Run" mode, making no changes, unless you specify the "-r" or "--remove" in the command line arguments.
In that mode, it scans the directory tree or directory trees that were specified in the command line, for files with the same size.
Then it builds a dictionary with their file sizes as index, creating a list of duplicates using only that criterion.
At the same time, it's showing the progress, for each directory, listing the total size of the duplicate files it found so far using that method.
Once it's done, it calculates the CRC32 or MD5 hashes of all the files in the dictionary, to find which are trully duplicates, regardless of their filenames.
Then it replaces the duplicate files with a symbolic link, pointing to a single copy of the file.
If you specify multiple directories in the command line, the first one will be considered as "master",
and the duplicates found in the other directories will be pointing to files on that one.
However, if there are also duplicate files in the first directory tree, those will be treated as well the same way, and the first one found will be kept,
while the subsequent ones will be replaced with symbolic links too.

An example of a dry-run with a single directory, using the faster (and less reliable) CRC32 instead of the MD5, would be the following:

./find_duplicate_files_and_replace_them_with_symlinks.py -d path_containing_duplicate_files

If you'd like to remove the duplicate files in the above example just add the "--remove" argument:

./find_duplicate_files_and_replace_them_with_symlinks.py -d path_containing_duplicate_files --remove

If you'd like to dry-run a scan on 3 directories for duplicate files, using MD5 hashes instead of CRC32, you could do it using the following command:

./find_duplicate_files_and_replace_them_with_symlinks.py -d path1 -d path2 -d path3 -md5

And of course, to run the actual command and replace the duplicates you should use the "-r" or "--remove" argument in the above command:

./find_duplicate_files_and_replace_them_with_symlinks.py -d path1 -d path2 -d path3 -md5 --remove



Finally, the bash script "restore_original_files_in_place_of_symlinks.sh" is running only on the current folder and below, 
replacing all the symbolic links that it finds with a copy of the original files they're pointing to.
This was created to reverse the actions of the Python script, but you need to use it with caution, since it's not getting any arguments for path,
and it doesn't have a "dry-run" mode yet.
