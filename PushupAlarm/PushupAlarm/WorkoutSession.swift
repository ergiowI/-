import AVFoundation
import UIKit

/// Считает отжимания датчиком приближения (тот, что гасит экран у уха).
/// Телефон лежит на полу экраном вверх. Опустился к нему: датчик «закрыт».
/// Поднялся: «открыт», и отжимание засчитано.
final class WorkoutSession: ObservableObject {
    @Published private(set) var count: Int
    @Published private(set) var isDown = false
    @Published private(set) var finished = false
    @Published private(set) var sensorAvailable = true
    let target: Int

    private let sound = AlarmSound()
    private let speech = AVSpeechSynthesizer()
    private var observer: NSObjectProtocol?
    private var timer: Timer?
    private var downAt: Date?
    private var lastRep = Date.distantPast
    private var lastActivity = Date()
    private var lastNagPush = Date.distantPast
    private var running = false

    /// Нужно продержаться внизу хотя бы столько, чтобы взмах рукой не прокатил.
    private let minDownTime: TimeInterval = 0.25
    /// Минимум между повторами.
    private let minRepInterval: TimeInterval = 0.6
    /// Если столько секунд ничего не делаешь, снова начинает пищать.
    private let idleTimeout: TimeInterval = 20

    init() {
        target = Settings.target
        count = Settings.done
    }

    func begin() {
        guard !running else { return }
        running = true

        if count >= target { finish(); return }

        UIApplication.shared.isIdleTimerDisabled = true
        let device = UIDevice.current
        device.isProximityMonitoringEnabled = true
        sensorAvailable = device.isProximityMonitoringEnabled

        observer = NotificationCenter.default.addObserver(
            forName: UIDevice.proximityStateDidChangeNotification, object: device, queue: .main
        ) { [weak self] _ in self?.proximityChanged() }

        sound.start()
        pushNag()
        timer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { [weak self] _ in self?.tick() }
    }

    func close() {
        guard running else { return }
        running = false
        timer?.invalidate(); timer = nil
        if let observer { NotificationCenter.default.removeObserver(observer) }
        observer = nil
        UIDevice.current.isProximityMonitoringEnabled = false
        UIApplication.shared.isIdleTimerDisabled = false
        sound.stop()
    }

    // MARK: -

    private func proximityChanged() {
        guard !finished else { return }
        let near = UIDevice.current.proximityState
        let now = Date()
        if near {
            downAt = now
            isDown = true
        } else if let down = downAt {
            downAt = nil
            isDown = false
            guard now.timeIntervalSince(down) >= minDownTime,
                  now.timeIntervalSince(lastRep) >= minRepInterval else { return }
            lastRep = now
            rep()
        }
    }

    private func rep() {
        count += 1
        Settings.done = count
        lastActivity = Date()
        sound.stop()
        if count >= target {
            finish()
        } else {
            say("\(count)")
        }
    }

    private func finish() {
        finished = true
        AlarmService.endSession()
        close()
        say("Красава! Доброе утро")
    }

    private func tick() {
        guard running, !finished else { return }
        // Держим повторный будильник впереди, пока приложение открыто.
        if Date().timeIntervalSince(lastNagPush) > 30 { pushNag() }
        if Date().timeIntervalSince(lastActivity) > idleTimeout, !sound.isPlaying, !isDown {
            sound.start()
        }
    }

    private func pushNag() {
        lastNagPush = Date()
        Task { await AlarmService.scheduleNag(in: 90) }
    }

    private func say(_ text: String) {
        let u = AVSpeechUtterance(string: text)
        u.voice = AVSpeechSynthesisVoice(language: "ru-RU")
        u.rate = 0.55
        speech.stopSpeaking(at: .immediate)
        speech.speak(u)
    }
}
