---
title: 搴旂敤棰勮
description: 鐢ㄤ竴鏉″懡浠ゅ湪鏈湴棰勮 Skylattice 鐨勭綉椤典骇鍝侀潰锛屾煡鐪嬪彧璇荤ず渚嬪伐浣滃尯锛屽苟鐞嗚В浠?preview 鍒囧埌 live pairing 涔嬪悗浼氬彂鐢熶粈涔堝彉鍖栥€?robots: index, follow
alternates:
  - lang: en
    href: https://yscjrh.github.io/skylattice/app-preview/
  - lang: zh-CN
    href: https://yscjrh.github.io/skylattice/zh/app-preview/
jsonld: |
  {
    "@context": "https://schema.org",
    "@type": "SoftwareSourceCode",
    "name": "Skylattice App Preview",
    "description": "Skylattice 缃戦〉浜у搧闈㈢殑鍙鍒濇棰勮鍏ュ彛銆?,
    "codeRepository": "https://github.com/YSCJRH/skylattice",
    "softwareVersion": "0.4.1",
    "license": "https://github.com/YSCJRH/skylattice/blob/main/LICENSE",
    "inLanguage": "zh-CN"
  }
---

# 搴旂敤棰勮

濡傛灉浣犳兂鍏堢湅鐪?Skylattice 鐨勭綉椤典骇鍝侀潰鏄粈涔堟牱瀛愶紝鑰屼笉鏄厛閰嶇疆 GitHub OAuth銆乸airing 鏈湴 agent 鎴?hosted deployment锛屽氨浠庤繖閲屽紑濮嬨€?
## 涓€鏉″懡浠ょ殑鍏ュ彛

鍦ㄤ粨搴撴牴鐩綍鎵ц锛?
```powershell
npm install
npm run web:preview
```

鐒跺悗鎵撳紑 [http://localhost:3000/dashboard](http://localhost:3000/dashboard)銆?
杩欎細鍚姩鍚屼粨搴撶殑 `Next.js` 搴旂敤锛屽苟浠ュ彧璇?preview 妯″紡鍔犺浇涓€濂楀凡缁忓噯澶囧ソ鐨勪唬琛ㄦ€хず渚嬫暟鎹€?
Tracked proof data: [web-app-preview-state.json](https://github.com/YSCJRH/skylattice/blob/main/examples/redacted/web-app-preview-state.json)

## 浣犲彲浠ュ厛鐪嬪摢浜涢〉闈?
杩欎釜 preview 涓昏鏄负浜嗗府浣犲揩閫熷洖绛斾竴涓棶棰橈細杩欎釜缃戦〉浜у搧闈㈢湅璧锋潵鏄惁瓒冲鍙俊锛屽€煎緱缁х画娣卞叆锛?
寤鸿浼樺厛鎵撳紑杩欎簺璺敱锛?
- `/dashboard`锛氳澶囩姸鎬併€佹渶杩戝懡浠ゃ€乤pproval 鍘嬪姏銆乵emory activity
- `/tasks`锛歡overned task run 鐨勮〃闈㈠舰鎬佸拰浠ｈ〃鎬х粨鏋滃巻鍙?- `/radar`锛歴can銆乻chedule validate銆乺eplay銆乺ollback 鐨勫伐浣滃尯
- `/memory`锛歴earch銆乸rofile proposal銆乺eview-driven memory actions
- `/commands`锛氬懡浠よ处鏈拰鍗曟潯鍛戒护 drill-down
- `/connect`锛歱airing flow銆乸airing code 鍜?claimed device 鐘舵€?- `/devices` 涓?`/approvals`锛氭洿闀挎湡鐨勭鐞嗛〉

## 杩欎釜 Preview 鏄粈涔?
- 涓€涓湡瀹炰絾鍙鐨勭綉椤典骇鍝佸垵姝ュ叆鍙?- 涓€涓甫浠ｈ〃鎬?command銆乨evice銆乸airing銆乤pproval 鏁版嵁鐨?guest session
- 涓€涓湪 live setup 涔嬪墠鍏堣瘎浼颁俊鎭灦鏋勫拰浜や簰妯″瀷鐨勬柟寮?
## 杩欎釜 Preview 涓嶆槸浠€涔?
- 涓嶆槸 hosted runtime
- 涓嶆槸 live account session
- 榛樿涓嶄細杩炲埌鐪熷疄鐨勬湰鍦?agent
- 涓嶅厑璁哥洿鎺?queue live commands銆乺evoke live devices 鎴?resolve live approvals

杩欎釜 preview 鏄埢鎰忎繚鎸佸彧璇荤殑銆?
## 鍒囧埌 Live Mode 涔嬪悗浼氬彉浠€涔?
褰撲綘浠?preview 杩涘叆 live control锛屾灦鏋勫苟涓嶄細鍙橈紝鍙槸鏁版嵁浠庝唬琛ㄦ€ф牱渚嬪彉鎴愮湡瀹炶繍琛岄潰锛?
1. 鐢?GitHub 鐧诲綍
2. 鍒涘缓鐭椂 pairing code
3. 鍦ㄦ湰鍦扮敤 `skylattice web pair` claim 杩欎釜 code
4. 璁╂湰鍦?connector claim commands 骞跺洖浼?readiness

娴忚鍣ㄤ粛鐒朵笉浼氬彉鎴?runtime truth銆傜湡姝ｆ墽琛屼换鍔°€佺淮鎶?memory銆佸仛瀹℃壒鍜屾不鐞嗗垽鏂殑锛屼粛鐒舵槸閰嶅鍚庣殑鏈湴 Skylattice agent銆?
## 鐩稿叧椤甸潰

- [Web Control Plane](../web-control-plane.md)
- [蹇€熷紑濮媇(quickstart.md)
- [璇佹槑鏉愭枡](proof.md)
- [v0.4.1 Stable](releases/v0-4-1.md)
