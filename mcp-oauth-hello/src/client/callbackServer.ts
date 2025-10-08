/**
 * OAuth Callback Server
 *
 * 認可コードを受け取るためのローカルHTTPサーバー
 */

import http from 'http';

let server: http.Server | null = null;
let authorizationCode: string | null = null;
let codeResolve: ((code: string) => void) | null = null;
let codeReject: ((error: Error) => void) | null = null;

/**
 * コールバックサーバーを起動
 */
export async function startCallbackServer(port: number): Promise<void> {
  return new Promise((resolve, reject) => {
    server = http.createServer((req, res) => {
      const url = new URL(req.url!, `http://localhost:${port}`);

      if (url.pathname === '/callback') {
        const code = url.searchParams.get('code');
        const error = url.searchParams.get('error');

        if (error) {
          res.writeHead(400, { 'Content-Type': 'text/html' });
          res.end(`
            <html>
              <body>
                <h1>❌ Authorization Failed</h1>
                <p>Error: ${error}</p>
                <p>${url.searchParams.get('error_description') || ''}</p>
                <p>You can close this window.</p>
              </body>
            </html>
          `);
          if (codeReject) {
            codeReject(new Error(`OAuth error: ${error}`));
            codeReject = null;
            codeResolve = null;
          }
          return;
        }

        if (code) {
          authorizationCode = code;
          res.writeHead(200, { 'Content-Type': 'text/html' });
          res.end(`
            <html>
              <body>
                <h1>✅ Authorization Successful!</h1>
                <p>You can close this window and return to your terminal.</p>
                <script>window.close();</script>
              </body>
            </html>
          `);

          if (codeResolve) {
            codeResolve(code);
            codeResolve = null;
            codeReject = null;
          }
        } else {
          res.writeHead(400, { 'Content-Type': 'text/html' });
          res.end(`
            <html>
              <body>
                <h1>❌ Invalid Callback</h1>
                <p>No authorization code received.</p>
              </body>
            </html>
          `);
        }
      } else {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('Not Found');
      }
    });

    server.listen(port, () => {
      console.error(`✅ Callback server listening on http://localhost:${port}`);
      resolve();
    });

    server.on('error', (error) => {
      reject(error);
    });
  });
}

/**
 * コールバックサーバーを停止
 */
export function stopCallbackServer(): void {
  if (server) {
    server.close();
    server = null;
    console.error('🛑 Callback server stopped');
  }
}

/**
 * 認可コードを取得（コールバック待機）
 */
export async function waitForAuthorizationCode(): Promise<string> {
  if (authorizationCode) {
    const code = authorizationCode;
    authorizationCode = null;
    return code;
  }

  return new Promise((resolve, reject) => {
    codeResolve = resolve;
    codeReject = reject;
  });
}
