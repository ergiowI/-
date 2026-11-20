import AlarmKit
import SwiftUI

struct PushupMetadata: AlarmMetadata {}

/// Работа с системными будильниками (AlarmKit, iOS 26+).
///
/// Главная хитрость: пока отжимания не сделаны, в системе всегда висит
/// «злой» повторный будильник на ближайшие 1–2 минуты. Нажал «Стоп» — он
/// зазвонит снова. Убил приложение — зазвонит снова. Отпускает только
/// выполненная норма.
enum AlarmService {
    static let manager = AlarmManager.shared

    // MARK: - Разрешение

    static func requestAuthorization() async -> Bool {
        switch manager.authorizationState {
        case .authorized: return true
        case .denied: return false
        case .notDetermined:
            return (try? await manager.requestAuthorization()) == .authorized
        @unknown default: return false
        }
    }

    // MARK: - Основной будильник (каждый день)

    static func scheduleMain(hour: Int, minute: Int) async throws {
        cancelMain()
        let id = UUID()
        let allDays: [Locale.Weekday] = [.monday, .tuesday, .wednesday, .thursday, .friday, .saturday, .sunday]
        let schedule = Alarm.Schedule.relative(.init(
            time: .init(hour: hour, minute: minute),
            repeats: .weekly(allDays)
        ))
        _ = try await manager.schedule(
            id: id,
            configuration: configuration(id: id, schedule: schedule, title: "Подъём! \(Settings.target) отжиманий")
        )
        Settings.mainAlarmID = id
    }

    static func cancelMain() {
        if let id = Settings.mainAlarmID { try? manager.cancel(id: id) }
        Settings.mainAlarmID = nil
    }

    /// Разовый будильник для проверки.
    static func scheduleTest(in seconds: TimeInterval) async throws {
        let id = UUID()
        _ = try await manager.schedule(
            id: id,
            configuration: configuration(id: id, schedule: .fixed(Date().addingTimeInterval(seconds)),
                                         title: "Тест! \(Settings.target) отжиманий")
        )
    }

    // MARK: - Повторный «злой» будильник

    /// Переносит повторный будильник на `seconds` секунд от текущего момента.
    static func scheduleNag(in seconds: TimeInterval) async {
        guard Settings.sessionActive else { return }
        cancelExtraAlarms()
        let id = UUID()
        Settings.nagAlarmID = id
        let left = max(Settings.target - Settings.done, 1)
        _ = try? await manager.schedule(
            id: id,
            configuration: configuration(id: id, schedule: .fixed(Date().addingTimeInterval(seconds)),
                                         title: "Не так быстро! Осталось \(left)")
        )
        // Пока планировали, норму могли закрыть, тогда убираем.
        if !Settings.sessionActive || Settings.nagAlarmID != id {
            try? manager.cancel(id: id)
        }
    }

    /// Норма выполнена: убираем все повторные будильники.
    static func endSession() {
        Settings.sessionActive = false
        Settings.done = 0
        Settings.nagAlarmID = nil
        cancelExtraAlarms()
    }

    /// Отменяет все будильники, кроме основного ежедневного.
    private static func cancelExtraAlarms() {
        let main = Settings.mainAlarmID
        for alarm in (try? manager.alarms) ?? [] where alarm.id != main {
            try? manager.cancel(id: alarm.id)
        }
    }

    // MARK: - Внешний вид

    private static func configuration(id: UUID, schedule: Alarm.Schedule, title: LocalizedStringResource)
        -> AlarmManager.AlarmConfiguration<PushupMetadata>
    {
        let alert = AlarmPresentation.Alert(
            title: title,
            stopButton: AlarmButton(text: "Стоп", textColor: .white, systemImageName: "xmark"),
            secondaryButton: AlarmButton(text: "Отжаться", textColor: .black,
                                         systemImageName: "figure.strengthtraining.traditional"),
            secondaryButtonBehavior: .custom
        )
        let attributes = AlarmAttributes<PushupMetadata>(
            presentation: AlarmPresentation(alert: alert),
            metadata: PushupMetadata(),
            tintColor: .orange
        )
        return AlarmManager.AlarmConfiguration(
            countdownDuration: nil,
            schedule: schedule,
            attributes: attributes,
            stopIntent: StopAlarmIntent(alarmID: id.uuidString),
            secondaryIntent: OpenWorkoutIntent(alarmID: id.uuidString),
            sound: .default
        )
    }
}
