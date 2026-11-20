import AlarmKit
import AppIntents

/// Кнопка «Стоп». Будильник замолкает, но через минуту зазвонит снова.
struct StopAlarmIntent: LiveActivityIntent {
    static var title: LocalizedStringResource = "Стоп"
    static var isDiscoverable = false

    @Parameter(title: "ID будильника")
    var alarmID: String

    init(alarmID: String) { self.alarmID = alarmID }
    init() { self.alarmID = "" }

    func perform() async throws -> some IntentResult {
        if let id = UUID(uuidString: alarmID) { try? AlarmManager.shared.stop(id: id) }
        Settings.startSessionIfNeeded()
        await AlarmService.scheduleNag(in: 60)
        return .result()
    }
}

/// Кнопка «Отжаться». Открывает приложение с экраном отжиманий.
struct OpenWorkoutIntent: LiveActivityIntent {
    static var title: LocalizedStringResource = "Отжаться"
    static var isDiscoverable = false
    static var openAppWhenRun = true

    @Parameter(title: "ID будильника")
    var alarmID: String

    init(alarmID: String) { self.alarmID = alarmID }
    init() { self.alarmID = "" }

    func perform() async throws -> some IntentResult {
        if let id = UUID(uuidString: alarmID) { try? AlarmManager.shared.stop(id: id) }
        Settings.startSessionIfNeeded()
        // Страховка: если закроешь приложение, не доделав, будильник вернётся.
        await AlarmService.scheduleNag(in: 120)
        return .result()
    }
}
