//This code creates a 
// CloudWatch client using the aws-cloudwatch package and sends metrics to it.
const cloudwatch = require('aws-cloudwatch');

const cw = new cloudwatch({
  region: 'us-west-2',
});

cw.putMetricData({
  Namespace: 'AWS/ElasticBeanstalk/Environment',
  MetricName: 'CPUUtilization',
  Dimensions: [
    {
      Name: 'EnvironmentName',
      Value: process.env.ELASTIC_BEANSTALK_ENVIRONMENT_NAME,
    },
  ],
}, (err, data) => {
  if (err) console.error(err);
  else console.log(data);
});