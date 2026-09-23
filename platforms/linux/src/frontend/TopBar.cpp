/*
 *  OpenBangla Keyboard
 *  Copyright (C) 2016-2018 Muhammad Mominul Huque <mominul2082@gmail.com>
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

#include <QApplication>
#include <QDesktopServices>
#include <QJsonDocument>
#include <QJsonObject>
#include <QMessageBox>
#include <QMouseEvent>
#include <QFileDialog>
#include <QMenu>
#include <QDir>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QScreen>
#include <QTimer>
#include <QUrl>
#include <QVersionNumber>
#include "TopBar.h"
#include "Layout.h"
#include "Settings.h"
#include "FileSystem.h"
#include "LayoutViewer.h"
#include "AboutDialog.h"
#include "SettingsDialog.h"
#include "LayoutConverter.h"
#include "ui_TopBar.h"

static const QString GITHUB_REPOSITORY = BONGO_GITHUB_REPOSITORY;

TopBar::TopBar(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::TopBar) {
  ui->setupUi(this);

  gLayout = new Layout();
  gSettings = new Settings();
  networkManager = new QNetworkAccessManager(this);

  /* Dialogs */
  aboutDialog = new AboutDialog(Q_NULLPTR);
  layoutViewer = new LayoutViewer(Q_NULLPTR);
  settingsDialog = new SettingsDialog(Q_NULLPTR);

  ui->buttonIcon->installEventFilter(this);

  SetupTopBar();
  SetupPopupMenus();
  DataMigration();

  if (!GITHUB_REPOSITORY.isEmpty() && gSettings->getUpdateCheck()) {
    checkForUpdate(false);
  }
}

TopBar::~TopBar() {
  /* Dialogs */
  delete layoutViewer;
  delete settingsDialog;
  delete aboutDialog;

  delete gLayout;
  delete gSettings;

  delete ui;
}

void TopBar::SetupTopBar() {
  this->setWindowFlags(Qt::Window | Qt::FramelessWindowHint | Qt::WindowStaysOnTopHint);
  this->setFixedSize(QSize(this->width(), this->height()));

  if (gSettings->getTopBarWindowPosition() == QPoint(0, 0)) {
    int width = this->frameGeometry().width();
    int height = this->frameGeometry().height();
    if (QScreen *screen = QGuiApplication::primaryScreen()) {
      const QRect available = screen->availableGeometry();
      this->setGeometry(available.center().x() - (width / 2),
                        available.center().y() - (height / 2), width, height);
    }
  } else {
    move(gSettings->getTopBarWindowPosition());
  }
}

void TopBar::checkForUpdate(bool notifyIfCurrent) {
  if (GITHUB_REPOSITORY.isEmpty()) {
    QMessageBox::information(this, "Bongo", "Updates are not configured for this local build. See README.md for release-build instructions.");
    return;
  }
  notifyWhenCurrent = notifyWhenCurrent || notifyIfCurrent;
  if (updateReply) {
    return;
  }

  const QUrl url(QString("https://api.github.com/repos/%1/releases/latest").arg(GITHUB_REPOSITORY));
  QNetworkRequest request(url);
  request.setRawHeader("Accept", "application/vnd.github+json");
  request.setRawHeader("User-Agent", QString("Bongo-Linux/%1").arg(qApp->applicationVersion()).toUtf8());
  updateReply = networkManager->get(request);
  QTimer *timeout = new QTimer(updateReply);
  timeout->setSingleShot(true);
  connect(timeout, &QTimer::timeout, updateReply, &QNetworkReply::abort);
  timeout->start(15000);

  connect(updateReply, &QNetworkReply::finished, this, [this]() {
    QNetworkReply *reply = updateReply;
    updateReply = nullptr;
    const bool reportCurrent = notifyWhenCurrent;
    notifyWhenCurrent = false;

    if (!reply) {
      return;
    }
    const QByteArray response = reply->readAll();
    const bool failed = reply->error() != QNetworkReply::NoError;
    reply->deleteLater();

    const QJsonObject release = QJsonDocument::fromJson(response).object();
    const QString tag = release.value("tag_name").toString();
    const QUrl releaseUrl(release.value("html_url").toString());
    if (failed || tag.isEmpty() || !releaseUrl.isValid()) {
      if (reportCurrent) {
        QMessageBox::warning(this, "Bongo", "Couldn’t check for updates. Check your internet connection and the GitHub Releases page, then try again.");
      }
      return;
    }

    QString latest = tag;
    if (latest.startsWith('v', Qt::CaseInsensitive)) {
      latest.remove(0, 1);
    }
    const QVersionNumber currentVersion = QVersionNumber::fromString(qApp->applicationVersion());
    const QVersionNumber latestVersion = QVersionNumber::fromString(latest);
    if (latestVersion.isNull() || currentVersion.isNull()) {
      if (reportCurrent) {
        QMessageBox::warning(this, "Bongo", "The release version could not be read. Open GitHub Releases and check manually.");
      }
    } else if (QVersionNumber::compare(latestVersion, currentVersion) > 0) {
      const QMessageBox::StandardButton choice = QMessageBox::information(
          this, "Bongo update available",
          QString("Bongo %1 is available. Open the release page to download it?").arg(latest),
          QMessageBox::Open | QMessageBox::Cancel, QMessageBox::Open);
      if (choice == QMessageBox::Open) {
        QDesktopServices::openUrl(releaseUrl);
      }
    } else if (reportCurrent) {
      QMessageBox::information(this, "Bongo", QString("Bongo %1 is up to date.").arg(qApp->applicationVersion()));
    }
  });
}

void TopBar::SetupPopupMenus() {
  // Layout Popup Menu
  layoutMenu = new QMenu("Select keyboard layout", this);
  layoutMenu->setIcon(QIcon(":/images/keyboard_layout.png"));
  connect(layoutMenu, &QMenu::aboutToHide, [=]() {
    ui->buttonSetLayout->setChecked(false);
  });

  layoutMenuInstall = new QAction("Install a layout", this);
  layoutMenuLayoutsGroup = new QActionGroup(this);
  for (auto &layoutMenuLayout : layoutMenuLayouts) {
    layoutMenuLayout = new QAction(this);
    layoutMenuLayout->setVisible(false);
    layoutMenuLayout->setCheckable(true);
    layoutMenuLayoutsGroup->addAction(layoutMenuLayout);
    connect(layoutMenuLayout, SIGNAL(triggered()), this, SLOT(layoutMenuLayouts_clicked()));
  }
  RefreshLayouts();
  connect(layoutMenuInstall, SIGNAL(triggered()), this, SLOT(layoutMenuInstall_clicked()));

  // Icon Button Popup Menu
  iconMenuLayout = new QAction("About current keyboard layout", this);
  connect(iconMenuLayout, SIGNAL(triggered()), this, SLOT(iconMenuLayout_clicked()));

  iconMenuAbout = new QAction("About Bongo", this);
  connect(iconMenuAbout, SIGNAL(triggered()), this, SLOT(iconMenuAbout_clicked()));

  iconMenuUpdate = new QAction("Check for updates", this);
  connect(iconMenuUpdate, &QAction::triggered, [=]() {
    checkForUpdate(true);
  });

  iconMenu = new QMenu(this);
  iconMenu->addAction(iconMenuLayout);
  iconMenu->addAction(iconMenuAbout);
  iconMenu->addAction(iconMenuUpdate);  
}

void TopBar::RefreshLayouts() {
  layoutMenu->clear();
  LayoutList list;
  list = gLayout->searchLayouts();

  QString selectedLayout = gSettings->getLayoutName();

  for (int k = 0; k < MaxLayoutFiles; ++k) {
    if (k < list.count()) {
      QString name = list[k];
      layoutMenuLayouts[k]->setText(name);
      layoutMenuLayouts[k]->setVisible(true);
      // Select previously selected layout
      if (name == selectedLayout) {
        layoutMenuLayouts[k]->setChecked(true);
        gLayout->setLayout(name);
      }
    } else {
      layoutMenuLayouts[k]->setVisible(false);
    }
    layoutMenu->addAction(layoutMenuLayouts[k]);
  }
  layoutMenu->addSeparator();
  layoutMenu->addAction(layoutMenuInstall);
}

void TopBar::layoutMenuLayouts_clicked() {
  /**
   * From Qt version 5.10, Qt automatically adds shortcuts to
   * menu items. For that Qt includes a `&` character. So when
   * we use QAction::text() function, we get a string including
   * a `&` character and we mess all things up.
   *
   * See issue #17
   */

  QAction *action = qobject_cast<QAction *>(sender());

  QString layoutName = action->text();
  if (layoutName.contains("&")) {
    layoutName.replace("&", "");
  }

  gLayout->setLayout(layoutName);
  action->setChecked(true);
  layoutViewer->refreshLayoutViewer();
}

void TopBar::layoutMenuInstall_clicked() {
  QString fileName = QFileDialog::getOpenFileName(Q_NULLPTR, "Select Keyboard Layout", QDir::homePath(),
                                                  "Avro Keyboard 5 Keyboard Layout (*.avrolayout)");
  LayoutConverter conv;
  if (fileName.contains(".avrolayout") && fileName != "") {
    ConversionResult res = conv.convertAvroLayout(fileName);
    switch (res) {
    case Ok:
      QMessageBox::information(Q_NULLPTR, "Bongo", "Layout Installed Successfully",
                               QMessageBox::Ok);
      break;
    case UnsupportedLayout:
      QMessageBox::critical(Q_NULLPTR,
                            "Bongo",
                            "Unsupported Layout file!\nBongo only supports Avro Keyboard 5 layouts.",
                            QMessageBox::Ok);
      break;
    case OpenError:
      QMessageBox::critical(Q_NULLPTR, "Bongo",
                            "An error occurred while opening the layout file!", QMessageBox::Ok);
      break;
    case SaveError:
      QMessageBox::critical(Q_NULLPTR, "Bongo", "Error occurred while saving the file!",
                            QMessageBox::Ok);
      break;
    }
  }
  RefreshLayouts();
}

void TopBar::iconMenuLayout_clicked() {
  layoutViewer->showLayoutInfoDialog();
}

void TopBar::iconMenuAbout_clicked() {
  aboutDialog->show();
}

void TopBar::on_buttonIcon_clicked() {
  // Check if this is not a position change event. If it is, then ignore it.
  if(!positionChanged) {
    QPoint point;
    point = this->pos();
    point.setX(point.x() + ui->buttonIcon->geometry().x());
    point.setY(point.y() + this->height());
    iconMenu->exec(point);
  }
}

void TopBar::closeEvent(QCloseEvent *event) {
  gSettings->setTopBarWindowPosition(this->pos());
  event->accept();
}

bool TopBar::eventFilter(QObject *object, QEvent *event) {
  if (object == ui->buttonIcon) {
    if (event->type() == QEvent::MouseButtonPress) {
      canMoveTopbar = true;
      positionChanged = false; // reset
      QMouseEvent *e = (QMouseEvent *) event;
      pressedMouseX = e->x();
      pressedMouseY = e->y();
      event->accept();
    } else if (event->type() == QEvent::MouseMove) {
      if (canMoveTopbar) {
        QMouseEvent *e = (QMouseEvent *) event;
        ui->buttonIcon->setCursor(Qt::ClosedHandCursor);
        move(e->globalX() - pressedMouseX, e->globalY() - pressedMouseY);
        positionChanged = true;
      }
    } else if (event->type() == QEvent::MouseButtonRelease) {
      canMoveTopbar = false;
      ui->buttonIcon->setCursor(Qt::ArrowCursor);
      event->accept();
    }
  }

  return QObject::eventFilter(object, event);
}

void TopBar::on_buttonSetLayout_clicked() {
  QPoint point;
  point = this->pos();
  point.setX(point.x() + ui->buttonSetLayout->geometry().x());
  point.setY(point.y() + this->height());
  layoutMenu->exec(point);
}

void TopBar::on_buttonShutdown_clicked() {
  QApplication::exit();
}

void TopBar::on_buttonViewLayout_clicked() {
  layoutViewer->refreshLayoutViewer();
  layoutViewer->show();
}

void TopBar::on_buttonSettings_clicked() {
  settingsDialog->updateSettings();
  settingsDialog->show();
}

/**
 * OBK from version 2 onwards reads and stores user data in a different directory
 * the following XDG specification.
 * This function checks and migrates data files into the new user data directory.
 **/
void TopBar::DataMigration() {
  UserFolders usr;
  LayoutConverter converter;
  if(gSettings->getPreviousUserDataRemains()) {
    QDir previousUserDataPath = QDir(environmentVariable("HOME", "") + "/.Bongo");
    if(previousUserDataPath.exists()) {
      // Handle the data files.
      bool migrationSucceeded =
          migrateFile("phonetic-candidate-selection.json", previousUserDataPath, usr.dataPath()) &&
          migrateFile("autocorrect.json", previousUserDataPath, usr.dataPath());
      // Convert old layout files if present.
      previousUserDataPath.cd("Layouts");
      QStringList list = previousUserDataPath.entryList(QStringList("*.json"));
      if(!list.empty()) {
        for(auto& file : list) {
          QString path = previousUserDataPath.path() + "/" + file;

          if(converter.convertLayoutFormat(path) != Ok) {
            migrationSucceeded = false;
            QMessageBox::critical(Q_NULLPTR, "Bongo",
                            QString("An error occurred while converting %1 layout!").arg(file), QMessageBox::Ok);
            break;
          }
        }
      }
      if (migrationSucceeded) {
        QMessageBox::information(Q_NULLPTR, "Bongo", "User data files were migrated successfully.",
                                 QMessageBox::Ok);
        // Keep the legacy directory as a backup; do not delete user data automatically.
        gSettings->setPreviousUserDataRemains(false);
        RefreshLayouts();
      } else {
        QMessageBox::critical(Q_NULLPTR, "Bongo",
                              "Some user data could not be migrated. The original files were left unchanged.",
                              QMessageBox::Ok);
      }
    }
  }
}
