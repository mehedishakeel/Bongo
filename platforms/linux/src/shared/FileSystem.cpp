/*
 *  OpenBangla Keyboard
 *  Copyright (C) 2016 Muhammad Mominul Huque <mominul2082@gmail.com>
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "FileSystem.h"
#include <QSaveFile>

QString LayoutsFilePath() {
    return "/usr/share/bongo/layouts";
}

QString AvroPhoneticLayoutPath() {
    return "/usr/share/bongo/layouts/avrophonetic.json";
}

QString DatabasePath() {
    return "/usr/share/bongo/data";
}

QString DictionaryPath() {
    return "/usr/share/bongo/data/dictionary.json";
}

QString SuffixDictPath() {
    return "/usr/share/bongo/data/suffix.json";
}

QString RegexDictPath() {
    return "/usr/share/bongo/data/regex.json";
}

QString AutoCorrectFilePath() {
    return "/usr/share/bongo/data/autocorrect.json";
}

QString environmentVariable(const char *varName, const QString &defaultValue)
{
    QByteArray value = qgetenv(varName);
    if (value.isNull())
        return defaultValue;
    return QString::fromLocal8Bit(value);
}

/// Copy the `fileName` from `src` to `dst`.
/// This function overwrites if the file already exists in the destination.
bool migrateFile(const QString &fileName, const QDir &src, const QDir &dst) {
    const QString srcFile = src.filePath(fileName);
    const QString dstFile = dst.filePath(fileName);
    if (!QFile::exists(srcFile)) {
        return true;
    }

    QFile input(srcFile);
    QSaveFile output(dstFile);
    if (!input.open(QIODevice::ReadOnly) || !output.open(QIODevice::WriteOnly)) {
        return false;
    }

    while (!input.atEnd()) {
        const QByteArray chunk = input.read(64 * 1024);
        if (chunk.isEmpty() && input.error() != QFile::NoError) {
            output.cancelWriting();
            return false;
        }
        if (output.write(chunk) != chunk.size()) {
            output.cancelWriting();
            return false;
        }
    }
    return output.commit();
}
