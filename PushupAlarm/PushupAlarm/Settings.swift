import Foundation

/// Общее состояние приложения. Хранится в UserDefaults, чтобы его видели
/// и экраны, и интенты будильника (они работают в том же процессе).
enum Settings {
    private static let d = UserDefaults.standard

    /// Сколько отжиманий нужно сделать.
    static var target: Int {
        get { let v = d.integer(forKey: "target"); return v > 0 ? v : 20 }
        set { d.set(newValue, forKey: "target") }
    }

    /// Будильник прозвенел, а отжимания ещё не сделаны.
    static var sessionActive: Bool {
        get { d.bool(forKey: "sessionActive") }
        set { d.set(newValue, forKey: "sessionActive") }
    }

    /// Сколько уже сделано в текущей сессии.
    static var done: Int {
        get { d.integer(forKey: "done") }
        set { d.set(newValue, forKey: "done") }
    }

    static var mainAlarmID: UUID? {
        get { d.string(forKey: "mainAlarmID").flatMap(UUID.init(uuidString:)) }
        set { d.set(newValue?.uuidString, forKey: "mainAlarmID") }
    }

    static var nagAlarmID: UUID? {
        get { d.string(forKey: "nagAlarmID").flatMap(UUID.init(uuidString:)) }
        set { d.set(newValue?.uuidString, forKey: "nagAlarmID") }
    }

    static func startSessionIfNeeded() {
        guard !sessionActive else { return }
        done = 0
        sessionActive = true
    }
}
