/**
 * Browser Opener
 *
 * クロスプラットフォーム対応のブラウザ起動ユーティリティ
 */

import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

/**
 * ブラウザでURLを開く
 *
 * プラットフォームに応じて適切なコマンドを実行
 */
export async function openBrowser(url: string): Promise<void> {
  const platform = process.platform;

  let command: string;

  switch (platform) {
    case 'darwin': // macOS
      command = `open "${url}"`;
      break;
    case 'win32': // Windows
      command = `start "" "${url}"`;
      break;
    default: // Linux and others
      command = `xdg-open "${url}"`;
      break;
  }

  try {
    await execAsync(command);
    console.error(`✅ Browser opened: ${url}`);
  } catch (error) {
    console.error(`❌ Failed to open browser: ${error}`);
    console.error(`Please manually open: ${url}`);
  }
}
