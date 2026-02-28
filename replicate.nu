#!/usr/bin/env nu

# Replicate `src` directory structure in `dst`.
#
# The script first recreates `src` directory structure inside `dst`,
# then symlinks each `src` file into those directories.
def main [
  dst: string # destination directory, create it manually
  --src (-s): string = "." # replication source directory
  --filter (-f): list<string> # file names to exclude, e.g. '[file_a file_b]'
  --exclude (-e): list<string> # directory names to exclude, e.g. idem.
]: [] {
  if not ($dst | path exists) { mkdir $dst }
  dirs $src $dst ($exclude | default []) | files $src $dst ($filter | default [])
  "Success!"
}

def dirs [src: string dst: string to_exclude: list<string>]: [] {
  ^find $src -type d
  | lines
  | each { path split }
  | window 2 -r
  | do {|fst rst|
    $rst | reduce --fold $fst {|its acc|
      (
        if ($its.1 | length) > ($its.0 | length) {
          $acc | drop
        } else {
          $acc
        }
      ) | append $its.1
    }
  } ($in | first) ($in | skip)
  | where ($it | all {|$it| $to_exclude | all { $in != $it } })
  | tee {
      let dir = [$dst ...($in | skip)] | path join | path expand
      mkdir -v $dir
  }
}

def files [src: string dst: string filter: list<string>]: [list<string> -> any] {
  let included = $in
  ^find $src -type f -o -type l
  | lines
  | each { path split }
  | where {|it| $filter | all { $in != ($it | last) } }
  | where {|it| $included | any {$in == ($it | drop) }}
  | each {
    let tgt = $in | path join | path expand
    let lnk = [$dst ...($in | skip)] | path join | path expand
    ^ln -vs $tgt $lnk | print -e
  }
}
