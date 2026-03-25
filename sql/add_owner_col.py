
from app.database import engine
from sqlalchemy import text

def run_migration():
    with engine.connect() as conn:
        print("Checking if column exists...")
        try:
            conn.execute(text('ALTER TABLE "LabCenters" ADD COLUMN "OwnerUserID" INTEGER UNIQUE REFERENCES "Users"("UserID");'))
            conn.commit()
            print("Column added successfully.")
        except Exception as e:
            conn.rollback()
            print(f"Error adding column, might already exist: {e}")

if __name__ == "__main__":
    run_migration()
