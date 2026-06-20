import { Component, ReactNode } from 'react';

type ErrorBoundaryState = {
  error: Error | null;
};

export class ErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error) {
    console.error('[ErrorBoundary]', error);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="app-error-boundary">
          <div>
            <span>页面异常</span>
            <h2>当前视图加载失败</h2>
            <p>{this.state.error.message || '出现未知错误，请刷新页面或切换到其他模块。'}</p>
            <button className="primary-button" type="button" onClick={() => this.setState({ error: null })}>重试当前页面</button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
