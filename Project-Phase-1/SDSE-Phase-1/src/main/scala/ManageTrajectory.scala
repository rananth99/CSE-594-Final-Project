
import org.apache.log4j.{Level, Logger}
import org.apache.spark.sql.functions.{col, explode}
import org.apache.spark.sql.{DataFrame, SparkSession}

object ManageTrajectory {

  Logger.getLogger("org.spark_project").setLevel(Level.WARN)
  Logger.getLogger("org.apache").setLevel(Level.WARN)
  Logger.getLogger("akka").setLevel(Level.WARN)
  Logger.getLogger("com").setLevel(Level.WARN)


  def loadTrajectoryData(spark: SparkSession, filePath: String): DataFrame =
    {
      var trajectoryDf = spark.read
        .option("multiLine", true)
        .json(filePath)
      val data = trajectoryDf
        .withColumn("trajectory", explode(trajectoryDf("trajectory")))
      trajectoryDf = data
        .withColumn("location", data("trajectory.location"))
        .withColumn("timestamp", data("trajectory.timestamp"))
        .drop("trajectory")
        .withColumn("latitude", col("location").getItem(0))
        .withColumn("longitude", col("location").getItem(1))

      trajectoryDf.createOrReplaceTempView("trajectory")
      trajectoryDf = spark.sql("SELECT trajectory_id, vehicle_id,location,ST_POINT(latitude, longitude) AS point, timestamp FROM trajectory")
      trajectoryDf
    }


  def getSpatialRange(spark: SparkSession, dfTrajectory: DataFrame, latMin: Double, lonMin: Double, latMax: Double, lonMax: Double): DataFrame =
  {
    /* TO DO */
    dfTrajectory.createOrReplaceTempView("Range_Table")
    var df=spark.sql(s"SELECT trajectory_id,vehicle_id,collect_list(timestamp) as timestamp,collect_list(location) as location  FROM Range_Table WHERE ST_Within(Range_Table.point, ST_PolygonFromEnvelope($latMin,$lonMin,$latMax,$lonMax)) group by trajectory_id, vehicle_id")
    df.show(numRows = 500,truncate = false)
    df // change the null to desired spark DataFrame object
  }


  def getSpatioTemporalRange(spark: SparkSession, dfTrajectory: DataFrame, timeMin: Long, timeMax: Long, latMin: Double, lonMin: Double, latMax: Double, lonMax: Double): DataFrame =
  {
    /* TO DO */
    dfTrajectory.createOrReplaceTempView("RangeTemporal_Table")
    var df = spark.sql(s"SELECT trajectory_id,vehicle_id,collect_list(timestamp) as timestamp,collect_list(location) as location FROM RangeTemporal_Table WHERE ST_Within(RangeTemporal_Table.point, ST_PolygonFromEnvelope($latMin,$lonMin,$latMax,$lonMax)) and RangeTemporal_Table.timestamp between $timeMin and $timeMax group by trajectory_id, vehicle_id ")
//    df.show(numRows = 500, truncate = false)
    df // change the null to desired spark DataFrame object
  }


  def getKNNTrajectory(spark: SparkSession, dfTrajectory: DataFrame, trajectoryId: Long, neighbors: Int): DataFrame =
  {
    /* TO DO */
    dfTrajectory.createOrReplaceTempView("KNN_Table")
    var df = spark.sql(s"SELECT b.trajectory_id,ST_Distance(a.point, b.point) as distance FROM KNN_Table a, KNN_Table b where a.trajectory_id = $trajectoryId and b.trajectory_id <> $trajectoryId")
    df.createOrReplaceTempView("table")
    df = spark.sql(s"SELECT trajectory_id, min(distance) as finalDistance FROM table group by trajectory_id order by finalDistance ASC limit $neighbors")
    df.createOrReplaceTempView("finalTable")
    df = spark.sql(s"SELECT trajectory_id FROM finalTable")
    df


     // change the null to desired spark DataFrame object
  }


}
