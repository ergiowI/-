import AVFoundation

/// Громкий писк внутри приложения, пока ты отжимаешься.
/// Звук генерируется в коде, поэтому отдельный аудиофайл не нужен.
final class AlarmSound {
    private var player: AVAudioPlayer?

    var isPlaying: Bool { player?.isPlaying ?? false }

    func start() {
        let session = AVAudioSession.sharedInstance()
        try? session.setCategory(.playback, mode: .default) // играет и в беззвучном режиме
        try? session.setActive(true)
        if player == nil {
            player = try? AVAudioPlayer(data: Self.makeBeepWAV())
            player?.numberOfLoops = -1
        }
        player?.volume = 1
        player?.play()
    }

    func stop() {
        player?.stop()
        player?.currentTime = 0
    }

    /// Секунда звука: пик-пик и пауза. 16 бит, моно, 44.1 кГц.
    private static func makeBeepWAV() -> Data {
        let sampleRate = 44_100
        let total = sampleRate
        var samples = [Int16](repeating: 0, count: total)
        let beeps: [(start: Double, length: Double)] = [(0.0, 0.15), (0.25, 0.15)]
        for beep in beeps {
            let from = Int(beep.start * Double(sampleRate))
            let count = Int(beep.length * Double(sampleRate))
            for i in 0..<count where from + i < total {
                let t = Double(i) / Double(sampleRate)
                let wave = sin(2 * .pi * 1_000 * t) > 0 ? 1.0 : -1.0 // меандр звучит злее синуса
                samples[from + i] = Int16(wave * 0.8 * Double(Int16.max))
            }
        }

        var data = Data()
        func put<T: FixedWidthInteger>(_ v: T) {
            var le = v.littleEndian
            withUnsafeBytes(of: &le) { data.append(contentsOf: $0) }
        }
        let dataSize = UInt32(total * 2)
        data.append(contentsOf: Array("RIFF".utf8)); put(UInt32(36) + dataSize)
        data.append(contentsOf: Array("WAVE".utf8))
        data.append(contentsOf: Array("fmt ".utf8)); put(UInt32(16))
        put(UInt16(1)); put(UInt16(1))                      // PCM, моно
        put(UInt32(sampleRate)); put(UInt32(sampleRate * 2)) // частота, байт в секунду
        put(UInt16(2)); put(UInt16(16))                     // выравнивание блока, бит на сэмпл
        data.append(contentsOf: Array("data".utf8)); put(dataSize)
        for s in samples { put(s) }
        return data
    }
}
