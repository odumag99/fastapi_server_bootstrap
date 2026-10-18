"""모든 테이블 모델.

여기서 import 해야 `Base.metadata` 에 테이블이 등록된다 (Alembic autogenerate 와 테스트의
`create_all` 이 필요로 한다). 새 모델 파일을 만들면 아래에 추가한다.
"""

from app.models.user import User

__all__ = ["User"]
