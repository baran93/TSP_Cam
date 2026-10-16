# TSP_Cam — Raspberry Pi Camera System

> Product brief written by the owner (baran93), original Polish wording, added 2026-10-16.
> Decisions in [DECISIONS.md](DECISIONS.md) take precedence over this brief; see [AGENTS.md](../AGENTS.md) §4.

## Cel projektu

Stworzenie nowoczesnego, lekkiego i niezawodnego systemu kamer terenowych dla **Traffic Survey Partners (TSP)**, który całkowicie zastąpi MotionEye.

System służy do ciągłego nagrywania ruchu drogowego na potrzeby badań MCC, TMC, ANPR oraz późniejszej analizy AI.

**Priorytety:** niezawodność, niskie zużycie energii, prostota obsługi, automatyzacja i bezpieczeństwo nagrań.

## Sprzęt

- Raspberry Pi Zero 2 W (512 MB RAM).
- Moduły kamer OV5647 5 MP — obecnie około 400 sztuk.
- Możliwość obsługi przyszłych modułów z autofocusem lub zoomem.
- Zewnętrzny pendrive USB do nagrywania.
- Moduł RTC do odmierzania czasu bez internetu.
- Zasilanie sieciowe podczas testów, docelowo akumulatorowe.

## System i nagrywanie

- Raspberry Pi OS Lite 32-bit (Bookworm lub Trixie — wybór po testach).
- libcamera + Picamera2 + sprzętowe kodowanie H.264.
- Rozdzielczości: 800×600, 1280×960, 720p i 1080p.
- Nagrywanie ciągłe, bez detekcji ruchu.
- Pliki MP4 dzielone według **pełnych godzin zegarowych**. Pierwszy plik może być krótszy.
- Automatyczny start nagrywania po uruchomieniu urządzenia i wykryciu USB.
- Nigdy nie nadpisywać ani automatycznie nie usuwać nagrań.
- Bezpieczne zamykanie plików i automatyczne odzyskiwanie po błędach.
- Stamp w prawym dolnym rogu: data, godzina, logo TSP i numer Boxu.
- Zachowanie zgodności materiału z istniejącymi systemami analizy AI.

## Komunikacja

**Bluetooth jest główną metodą komunikacji.**

Telefon technika z Androidem zapewnia dostęp do panelu i opcjonalnie internet przez Bluetooth PAN.

Wi-Fi działa jako awaryjny hotspot przez pierwsze 15 minut od uruchomienia kamery, po czym automatycznie się wyłącza.

Nagrywanie musi działać niezależnie od Bluetooth, Wi-Fi, internetu i panelu.

## Web Panel

Prosty, responsywny interfejs przeznaczony dla techników terenowych.

Funkcje:
- Podgląd kamery na żywo w niskiej rozdzielczości, około 2 FPS.
- Status nagrywania, RTC, USB, temperatury i błędów.
- Przeglądanie oraz wyszukiwanie istniejących nagrań.
- Wybór rozdzielczości, FPS i miejsca zapisu.
- Szacowany czas nagrywania na podstawie wolnej pamięci i bitrate.
- Wykrywanie systemów plików FAT32, exFAT, NTFS i ext4.
- Możliwość formatowania USB po wyraźnym potwierdzeniu, z zapisem operacji w logach.
- Automatyczna i ręczna synchronizacja czasu, w tym aktualizacja RTC.
- Ostrzeżenie o rozbieżności między czasem telefonu i kamery.
- Przycisk bezpiecznego wyłączenia całego Raspberry Pi.
- Prosty test poprawności instalacji.

## Instalacja i aktualizacje

System powinien instalować się na świeżym Raspberry Pi OS za pomocą jednej komendy.

Aktualizacje pobierane z GitHub Releases:
- Sprawdzanie dostępnej wersji.
- Wyświetlanie zmian i pytanie o potwierdzenie.
- Bezpieczna instalacja bez usuwania ustawień i nagrań.
- Automatyczny rollback w przypadku nieudanej aktualizacji.

Repozytorium projektu: **baran93/TSP_Cam** (prywatne).

## Diagnostyka i integracja

- Automatyczne monitorowanie nagrywania, USB, RTC i stanu urządzenia.
- Wykrywanie przerw w nagraniach i błędów enkodera.
- Zapisywanie logów na bieżąco i eksport na USB co godzinę.
- Automatyczne wykrywanie modułów kamer oraz dostępnych funkcji.
- Docelowa integracja z TSP OS — centralną ewidencją urządzeń, historią pracy i raportami.
- Możliwość synchronizacji diagnostyki przez internet telefonu.

## Zasady rozwoju

1. Niezawodność nagrywania jest ważniejsza niż dodatkowe funkcje.
2. Minimalizować zużycie CPU, RAM i energii.
3. W pierwszej kolejności wykorzystywać sprawdzone biblioteki i sterowniki.
4. Projektować system do obsługi setek kamer.
5. Testować zmiany na Raspberry Pi Zero 2 W przed wdrożeniem.
6. Nie wprowadzać zmian naruszających ustalone wymagania bez wcześniejszego uzgodnienia.
7. Analizować istniejące rozwiązania open source i profesjonalne systemy traffic survey.
8. Proponować ulepszenia, wykrywać błędy architektury i przewidywać sytuacje awaryjne.
9. Oddzielać funkcje już zaimplementowane od planowanych i eksperymentalnych.

**Docelowy rezultat:** kamera, którą technik uruchamia, ustawia kadr, sprawdza czas i poprawność nagrywania, a następnie pozostawia do samodzielnej pracy. System powinien zapewniać możliwie najwyższą niezawodność bez konieczności ciągłej obsługi.
