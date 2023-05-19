package com.wolApi.wolApi;

public class AppSettings {
    private static AppSettings INSTANCE;

    private AppSettings() {}

    public static synchronized AppSettings getInstance() {
        if (INSTANCE == null) {
            INSTANCE = new AppSettings();
        }

        return INSTANCE;
    }

    public String mainVerseURL(String bookNum, String chapterNum) {
        return String.format(
                "https://wol.jw.org/en/wol/b/r1/lp-e/nwtsty/%s/%s#study=discover",
                bookNum,
                chapterNum);
    }



}
