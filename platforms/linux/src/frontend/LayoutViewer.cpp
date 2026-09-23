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

#include <QCloseEvent>
#include <zstd.h>
#include "LayoutViewer.h"
#include "Settings.h"
#include "AboutFile.h"
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
  aboutDialog = new AboutFile(this);
  ui->labelImage->setAlignment(Qt::AlignCenter);
  this->setWindowFlags(Qt::Dialog | Qt::WindowTitleHint | Qt::WindowCloseButtonHint | Qt::WindowStaysOnTopHint);
  this->move(gSettings->getLayoutViewerWindowPosition());
}

LayoutViewer::~LayoutViewer() {
  delete aboutDialog;
  delete ui;
}

void LayoutViewer::refreshLayoutViewer() {
  image0.clear();
  image1.clear();
  ui->viewAltGr->setEnabled(false);
  ui->viewNormal->setEnabled(false);
  ui->labelImage->setText("");

  desc = gLayout->getDesc();
  this->setWindowTitle(desc.name + " :: Layout Viewer");

  if(desc.image0.size() != 0) {
    image0 = decodeAndDecompress(desc.image0);
    if(desc.image1.size() != 0) {
      image1 = decodeAndDecompress(desc.image1);
      ui->viewAltGr->setEnabled(true);
    }
    ui->viewNormal->setEnabled(true);
    on_viewNormal_clicked();
  } else {
    ui->labelImage->setText("No image to display!");
    this->resize(537, 152);
  }

  // This refreshes Layout Info Dialog
  aboutDialog->setDialogType(AboutLayout);
}

void LayoutViewer::showLayoutInfoDialog() {
  aboutDialog->setDialogType(AboutLayout);
  aboutDialog->show();
}

void LayoutViewer::closeEvent(QCloseEvent *event) {
  gSettings->setLayoutViewerWindowPosition(this->pos());
  event->accept();
}

void LayoutViewer::on_buttonAboutLayout_clicked() {
  showLayoutInfoDialog();
}

void LayoutViewer::on_viewNormal_clicked() {
  image.loadFromData(image0);
  ui->labelImage->setPixmap(QPixmap::fromImage(image));
  ui->labelImage->adjustSize();
  QSize size;
  size.setHeight(ui->labelImage->height() + ui->labelImage->y());
  size.setWidth(ui->labelImage->width());
  this->resize(size);
  ui->viewNormal->setChecked(true);
}

void LayoutViewer::on_viewAltGr_clicked() {
  image.loadFromData(image1);
  ui->labelImage->setPixmap(QPixmap::fromImage(image));
  ui->labelImage->adjustSize();
  QSize size;
  size.setHeight(ui->labelImage->height() + ui->labelImage->y());
  size.setWidth(ui->labelImage->width());
  this->resize(size);
  ui->viewAltGr->setChecked(true);
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
