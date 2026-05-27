local ext = get_current_extension_info()

project_ext(ext)

repo_build.prebuild_link {
    { "config", ext.target_dir.."/config" },
    { "docs", ext.target_dir.."/docs" },
    { "ku", ext.target_dir.."/ku" },
}

