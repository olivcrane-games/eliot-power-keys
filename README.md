# Eliot's Power Keys ⚡⌨️

A typing game for a 6-year-old who can't read yet, made for an old MacBook Air with a **Spanish keyboard**.

Everything is shown with pictures, colours and voice, so it works for a child who can't read yet.
- **Four languages:** Catalan (the main one), Spanish, German and English. You pick one with the flags, and every key he presses is spoken in that language.
- **On-screen Spanish Mac keyboard** with finger colours, including ñ, ç and the accent keys.
- **Worlds:** home row, letters, syllables, whole words, capitals, accents, numbers and sums, trackpad lessons, plus endless generated worlds after the hand-made ones.
- **Extras:** bosses (a gloop, a robot, a dragon, a pumpkin, a jack-in-the-box, an ice bat), secret levels, a Halloween world, a Toy Room, an Ice Kingdom, bees, stupid flying turtles when he makes a mistake, a robot cat and a walking fridge.
- **Rewards:** stars per world. Three perfect worlds earn one **real coin**, paid by a grown-up.
- **Recording:** a letter studio where the child records himself saying each letter, plus recorded family cheers.
- **Grown-up panel (⚙️):** settings, a learning report, voices and cheers.
- **Cloud save:** progress follows the child to any computer. It is encrypted in the browser with the game password before it's uploaded.

Everything is original artwork drawn in code: no Mario, no Power Rangers.

## How it's built

| File | What it is |
|---|---|
| `game.html` | The whole game: one HTML file with canvas, Web Speech API and no dependencies. Open it directly in a browser to play locally. |
| `build.py` | Builds the password-locked site into `dist/`. |
| `api/save.js` | Vercel function for cloud save. It stores already-encrypted saves in Vercel Blob. |
| `photos/faces.json` | *(not in git)* Optional family photos as `{"happy":"data:image/jpeg;base64,…", …}` |

### Photos
Without photos the game still works fine.

To use photos, put a `photos/faces.json` file in the folder. `build.py` encrypts the photos into `dist/faces.bin` with AES-GCM, using a key derived from the password with PBKDF2 (250k iterations), so they only appear after unlocking. The photo keys the game uses are:
- `happy`, `smug`, `wow`, `oops` (reactions)
- `e_laugh`, `e_grin`, `e_cuddle`, `e_tooth`, `e_castle`, `e_vers`, `e_boat`
- `mama1`, `mama2`, `papa1`, `papa2`, `papa3`, `hen`

## Build & deploy

```bash
pip install cryptography
python3 build.py <password>                       # writes dist/
cd dist && npx vercel --prod                      # deploy
```

For cloud save, create a **Vercel Blob** store and connect it to the project, so that `BLOB_READ_WRITE_TOKEN` is set. Without it the game still runs, and progress is just saved in each browser.

### Testing locally
Open `game.html?debug` in Chrome.
