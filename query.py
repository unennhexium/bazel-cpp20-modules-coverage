def format(target):
    return "\n".join(
        [
            str({
                k: {
                    "instrumented_files": v.instrumented_files.to_list(),
                    "metadata_files": v.metadata_files.to_list()
                }
            })
            for [k, v]
            in providers(target).items()
            if k == "InstrumentedFilesInfo"
        ]
    )
