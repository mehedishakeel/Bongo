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

#include <QGuiApplication>
#include <QScreen>
#include <zstd.h>
#include "LayoutViewer.h"
#include "Settings.h"
#include "base.hpp"
#include "ui_LayoutViewer.h"

namespace {
constexpr int MaximumEncodedImageSize = 32 * 1024 * 1024;
constexpr unsigned long long MaximumImageSize = 16ULL * 1024ULL * 1024ULL;
}

LayoutViewer::LayoutViewer(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::LayoutViewer) {
  ui->setupUi(this);
  ui->labelImage->setAlignment(Qt::AlignCenter);
  this->setWindowFlags(Qt::Dialog | Qt::WindowTitleHint | Qt::WindowCloseButtonHint | Qt::WindowStaysOnTopHint);
}

LayoutViewer::~LayoutViewer() {
  delete ui;
}

void LayoutViewer::refreshLayoutViewer() {
  image = QImage();
  ui->labelImage->setText("");
  ui->labelImage->setPixmap(QPixmap());

  desc = gLayout->getDesc();
  this->setWindowTitle(desc.name + " :: Layout Viewer");

  if (desc.name == "Bongo Phonetic") {
    image.load(":/images/bongo_phonetic_layout.png");
  } else if (!desc.image0.isEmpty()) {
    image.loadFromData(decodeAndDecompress(desc.image0));
  }

  if (image.isNull()) {
    ui->labelImage->setText("No layout guide is available.");
    ui->labelImage->setFixedSize(460, 120);
    this->setFixedSize(488, 148);
    return;
  }

  QSize maximum(1260, 540);
  QRect available;
  if (QScreen *screen = QGuiApplication::primaryScreen()) {
    available = screen->availableGeometry();
    maximum.setWidth(qMin(maximum.width(), available.width() - 80));
    maximum.setHeight(qMin(maximum.height(), available.height() - 120));
  }
  const QPixmap pixmap = QPixmap::fromImage(image).scaled(maximum, Qt::KeepAspectRatio, Qt::SmoothTransformation);
  ui->labelImage->setPixmap(pixmap);
  ui->labelImage->setFixedSize(pixmap.size());
  this->setFixedSize(pixmap.width() + 28, pixmap.height() + 28);
  if (!available.isNull()) {
    move(available.center() - rect().center());
  }
}

QByteArray LayoutViewer::decodeAndDecompress(const QByteArray &data) {
  if (data.size() > MaximumEncodedImageSize) {
    return {};
  }
  std::string decoded = base91::decode(std::string(data.data(), data.size()));
  const unsigned long long size = ZSTD_getFrameContentSize(decoded.data(), decoded.size());
  if (size == ZSTD_CONTENTSIZE_ERROR || size == ZSTD_CONTENTSIZE_UNKNOWN ||
      size > MaximumImageSize) {
    return {};
  }

  QByteArray imageData;
  imageData.resize(static_cast<int>(size));
  const size_t decompressed = ZSTD_decompress(imageData.data(), size, decoded.data(), decoded.size());
  if (ZSTD_isError(decompressed) || decompressed != size) {
    return {};
  }
  return imageData;
}
