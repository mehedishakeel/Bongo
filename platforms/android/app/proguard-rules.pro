# Bongo Proguard Rules
-keepclasseswithmembernames class * {
    native <methods>;
}

-keep class app.getbongo.ime.engine.** { *; }
-keep class app.getbongo.ime.model.** { *; }
-keep class app.getbongo.ime.BongoInputMethodService { *; }
-keep class app.getbongo.ime.ui.** { *; }

