#!/usr/bin/env nu

# Replicate `src` directory structure in `dst`.
#
# The script first recreates `src` directory structure inside `dst`,
# then symlinks each `src` file into those directories.
#
# Note: use one of the following commands to gather `--dry-run --json` output
#
# % dst=dir # destination directory
# % what=mkdir # or 'ln' to pick link creation report only
# % ./replicate.nu -dj $dst 2>&1 |
# >   jq -s --arg what $what \
# >     'reduce (.[] | to_entries[0]) as $it
# >       ({}; .[$it.key] += [$it.value])[$what]'
#
# ❯ ./replicate.nu -dj $dst 2>&1
# ¦ | lines
# ¦ | each {from json | transpose k v | first}
# ¦ | reduce -f {} {|it acc| $acc | merge deep -s append {$it.k: [$it.v]}}
# ¦ | select $what
# ¦ | to json
def main [
  dst: string # destination directory, create it manually
  --src (-s): string = "." # replication source directory
  --filter (-f): list<string> # file names to exclude, e.g. '[file_a file_b]'
  --exclude (-e): list<string> # directory names to exclude, e.g. idem.
  --absolute (-a) # whether to create absolute link targets
  --dry (-d) # do not perform any action, just print what will be created
  --json (-j) # report `--dry-run` as ndjson; see note above
]: [] {
  if not ($dst | path exists) and not $dry { mkdir $dst }
  let flt = $filter | default []
  [[]] | files $src $dst $flt $absolute $dry | print_files $dry $json
  dirs $src $dst ($exclude | default []) $dry
  | print_dirs $dry $json
  | files $src $dst $flt $absolute $dry
  | print_files $dry $json
  null
}

def dirs [src: string dst: string to_exclude: list<string>, dry: bool]: [
  any
  ->
  list<record<in: list<string> out: string>>
] {
  ^find $src -type d -printf %P\0
  | lines0
  | path split
  | window 2
  | do {|fst rst|
    $rst | reduce --fold $fst {|its acc|
      (
        if ($its.1 | length) > ($its.0 | length) {
          $acc | drop
        } else {
          $acc
        }
      ) | append [$its.1]
    }
  } ($in | first) ($in | skip)
  | where $it != []
  | where { all {|$it| $to_exclude | all { $in != $it } } }
  |
}

def print_dirs [dry: bool json: bool]: [
  list<record<in: list<string> out: string>>
  ->
  list<list<string>>
] {
  $in | par-each {
    if $dry {
      if $json {
        {mkdir: ($in | update in {path join})} | to json -r | print -e $in
      } else {
        print -e $"creating directory: \t'($in.out)'"
      }
    }
    $in.in
  }
}

def files [src: string dst: string filter: list<string>, abs: bool dry: bool]: [
  list<list<string>>
  ->
  list<record<string lnk: string tgt: string>>
] {
  let included = $in
  ^find $src '(' -type f -o -type l ')' -printf %P\0
  | lines0
  | path split
  | where {|it| $filter | all { $in != ($it | last) } }
  | where {|it| $included | any {$in == ($it | drop) }}
  | par-each {
    let lnk = [$dst ...$in] | path join
    let tgt = [$src ...$in] | path join | if $abs { path expand } else { path relative $lnk }
    if not $dry {
      ^ln -vs $tgt $lnk | print -e
    }
    {lnk: $lnk tgt: $tgt}
  }
}

def print_files [dry: bool json: bool]: [
  list<record<string lnk: string tgt: string>>
  ->
  any
] {
  $in | par-each {
    if $dry {
      if $json {
        {ln: $in} | to json -r | print -e $in
      } else {
        print -e $"creating symlink:\n- from:\t'($in.tgt)'\n- to:\t'($in.lnk)'"
      }
    }
  }
}

def lines0 []: [string -> list<string>] {
  split row (char -i 0)
}

def "path relative" [to: string]: [string -> string] {
  let pa = $in | path expand | path split
  let pb = $to | path expand | path split
  let fca_len = $pa | zip $pb | take while {|$it| $it.0 == $it.1 } | length
  0..<($pb | length | $in - $fca_len - 1) | each {".."}
  | append ($pa | skip $fca_len)
  | path join
}
