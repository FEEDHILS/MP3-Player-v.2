import sys, os
from PyQt6 import QtCore
from PyQt6.QtWidgets import *
from PyQt6 import uic
from pygame import mixer
import numpy as np
from pydub import AudioSegment

class ProductMusic(QMainWindow):
    def __init__(self):
        super(ProductMusic, self).__init__()
        uic.loadUi("design.ui", self)
        self.setFixedSize(870, 640)
        mixer.init()
        mixer.music.set_volume( self.slider_volume.value() )
        self.adressDict = dict() # Здесь каждой песне будет её конкретный адресс.
        self.currentSong = None
        self.pauseFlag = False
        self.lastSliderPos = 0 # При перемотке в mixer, сбрасывается get_pos, поэтому нам надо бы запоминать прошлую позицию слайдера.
        self.preload_music() # Презагружаем папку Music, в которую при желании можно закинуть музыку чтоб потом не добавлять по новой.

        # Подключаем виджеты
        self.bt_load.clicked.connect(self.load_music)
        self.bt_play.clicked.connect(self.play_music)
        self.bt_pause.clicked.connect(self.pause_music)
        self.bt_next.clicked.connect(self.next_music)
        self.bt_prev.clicked.connect(self.prev_music)
        self.list_music.itemDoubleClicked.connect(self.play_music)
        self.slider_time.sliderReleased.connect(self.sliderReleased)
        self.slider_volume.valueChanged.connect(self.VolumeChange)
        self.VolumeChange()
        
        
        #Update looop
        self.interval = 16 # 16 миллисекунд ≈ 60 fps
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(self.interval)
        self.timer.timeout.connect(self.updateUI)
        self.timer.start()

        # Это пригодится при визуализации
        self.lines = [self.line_1, self.line_2, self.line_3, self.line_4,
                    self.line_5, self.line_6, self.line_7, self.line_8, self.line_9]
        self.freq = [0 for i in range(9)]
        self.MaxFreq = 0

    # небольшой метод который подгружает всю музыку из папки Music
    def preload_music(self):
        for root, _, files in os.walk("Music"):
            for i in files:
                song_name = i[:-4]
                self.adressDict.update({song_name:"Music/{}".format(i)})
                self.list_music.addItem(song_name)


    def load_music(self):
        
        files = QFileDialog()
        files.setFileMode(QFileDialog.FileMode.ExistingFiles)
        names = files.getOpenFileNames(self, "Загрузите песни", filter="Audio Files (*.mp3 *.ogg *.wav))")

        for i in names[0]:
            song_name = i.split('/')[-1]
            song_name = song_name[:-4]
            self.adressDict.update({song_name: i}) # Сохраняем адресс чтобы потом использовать его при загрузки песни.
            self.list_music.addItem(song_name)



    def play_music(self):
        # Проверяем есть ли выбранный элемент в листе, если нет, выбираем первый в случае если лист не пустой.
        item = self.list_music.currentItem()
        if not item and self.list_music.count() > 0:
            self.list_music.setCurrentRow(0)
            self.play_music()
            return
        elif not item:
            return
        
        # Зачищаем данные, т.к запускается новая музыка
        self.lastSliderPos = 0
        self.pauseFlag = False
        self.currentSong = item.text()

        # Это пригодится при визуализации
        self.pydub = AudioSegment.from_file(self.adressDict[self.currentSong]).set_channels(1)
        self.samples = self.pydub.get_array_of_samples()


        length = len(self.pydub) # Длина песни в миллисекундах

        # Запускаем проигрыватель!
        mixer.music.load(self.adressDict[self.currentSong])
        mixer.music.play()

        # Обновляем виджеты
        self.slider_time.setMaximum(length)
        self.indicator_time.setText("{:02}:{:02}".format(length // 60000, length % 60000 // 1000))
        self.label.setText("Сейчас играет: {}".format(self.currentSong))


    def pause_music(self):
        if mixer.music.get_busy():
            mixer.music.pause()
            self.pauseFlag = True
            self.lastSliderPos = self.slider_time.value()
        
        elif self.pauseFlag:
            mixer.music.play(start = self.slider_time.value() / 1000)
            self.pauseFlag = False

# Два метода для расчета следующего и предыдущего элементов в списке, и переключении на них.
    def next_music(self):
        if self.currentSong != None:
            current = self.list_music.findItems(self.currentSong, QtCore.Qt.MatchFlag.MatchExactly)
            ind = self.list_music.row(current[0])

            new_ind = (ind+1) % self.list_music.count()
            self.list_music.setCurrentItem( self.list_music.item(new_ind) )
            self.play_music()

    def prev_music(self):
        if self.currentSong != None:
            current = self.list_music.findItems(self.currentSong, QtCore.Qt.MatchFlag.MatchExactly)
            ind = self.list_music.row(current[0])

            new_ind = self.list_music.count()-1 if (ind-1) < 0 else ind-1
            self.list_music.setCurrentItem( self.list_music.item(new_ind) )
            self.play_music()



    def sliderReleased(self):
        self.lastSliderPos = self.slider_time.value()
        if mixer.music.get_busy():
            mixer.music.play(start = self.lastSliderPos / 1000)

    # Все что связанно с громкостью
    def VolumeChange(self):
        volume = self.slider_volume.value()
        mixer.music.set_volume(volume / 100)
        self.indicator_volume.setText(str(volume))
        if volume > 50:
            self.bt_volume_0.hide()
            self.bt_volume_1.hide()
            self.bt_volume_2.show()
        elif volume > 0:
            self.bt_volume_0.hide()
            self.bt_volume_1.show()
            self.bt_volume_2.hide()
        else:
            self.bt_volume_0.show()
            self.bt_volume_1.hide()
            self.bt_volume_2.hide()
        

    def updateUI(self):
        # Обновляем слайдер таймлайна
        if mixer.music.get_busy() or self.pauseFlag:
            if not self.slider_time.isSliderDown() and not self.pauseFlag:
                self.slider_time.setValue(mixer.music.get_pos() + self.lastSliderPos)

            self.indicator_position.setText("{:02}:{:02}".format(self.slider_time.value() // 60000, 
                                                                 self.slider_time.value() % 60000 // 1000))
            
        # FFT and other bullshit
        if mixer.music.get_busy():
            smoothcoeff = 0.75 # Коэфф. сглаживания изменения
            self.fps = int(self.pydub.frame_rate * 0.001) # Кол-во семплов каждую миллисекунду
            start = ((mixer.music.get_pos() + self.lastSliderPos) - self.interval)*self.fps
            end = ((mixer.music.get_pos() + self.lastSliderPos) + self.interval)*self.fps

            # Всякое бывает
            if (end > len(self.pydub) * self.fps):
                end = len(self.pydub) * self.fps
            
            if (start < 0):
                start = 0
        
            SampleSlice = self.samples[start:end] # мощный
            
            SampleFFT = np.fft.rfft(SampleSlice)
            SampleFFT = np.abs(SampleFFT).real
            FFTStep = int(SampleFFT.size / 8)

            maximum = self.pydub.max

            # Считаем и "смягчаем" значение амплитуд разных частот.
            self.freq = [
            max(1, (smoothcoeff*self.freq[i] + SampleFFT[i*FFTStep:(i+1)*FFTStep].sum() * (1 - smoothcoeff)) / maximum * (i + 0.5))
            for i in range(8)
            ]

            # Просчитываем максимальную амплитуду (т.е громкость)
            self.MaxFreq = smoothcoeff*1.25 * self.MaxFreq + (1 - smoothcoeff*1.25) * max(SampleSlice)
            self.MaxFreq /= maximum * 0.1


            for i in range(8):
                self.lines[i].setGeometry( self.lines[i].x(), 280 - int(self.freq[i]), self.lines[i].width(), self.freq[i] )
            

            self.lines[8].setGeometry( self.lines[8].x(), 300 - max(1, int(self.MaxFreq * 400)), 
                                     self.lines[8].width(), max(1, int(self.MaxFreq * 400)) )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    our_app = ProductMusic()
    our_app.show()
    sys.exit(app.exec())